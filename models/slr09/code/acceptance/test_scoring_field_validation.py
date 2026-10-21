"""A scoring failure must remain visible without discarding other metrics."""
import unittest
from test_acceptance import reviewed,perfect
from evaluate_acceptance import score,validate_fields


class FieldScoringTests(unittest.TestCase):
    def setUp(self):
        self.bundle=reviewed();self.rows=self.bundle['records'];self.pred=perfect(self.rows)

    def test_joined_grounded_prediction_counts_as_wrong_field_instead_of_crashing(self):
        row=self.rows[0];pred=self.pred[0]
        extra=row['text'].split()[0]
        value=row['gold_fields']['location_text']+'; '+extra
        pred['adapted_result']['nara_result']['normalized_output']['location_text']=value
        pred['fusion_result']['incident_card_version_fields']['data']['location_text']=value
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertTrue(any(e['id']==row['id'] and e['field']=='location_text' for e in report['fields']['errors']))
        self.assertFalse(report['fields']['contract_errors'])
        self.assertLess(report['fields']['nonempty_exact'],1)

    def test_invented_model_value_is_a_contract_failure_not_a_scoring_exception(self):
        for place in ['normalized_output']:
            self.pred[0]['adapted_result']['nara_result'][place]['location_text']='Invented absent location'
        self.pred[0]['fusion_result']['incident_card_version_fields']['data']['location_text']='Invented absent location'
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertFalse(report['checks']['adapter_fusion_contract'])
        self.assertFalse(report['metric_targets_met'])
        self.assertTrue(any(x['reason']=='INVALID_EXTRACTED_FIELD' for x in report['fields']['contract_errors']))

    def test_human_reference_validator_remains_strict(self):
        row=self.rows[0];fields=dict(row['gold_fields'])
        fields['location_text']=fields['location_text']+'; '+row['text'].split()[0]
        with self.assertRaisesRegex(ValueError,'bersumber'):
            validate_fields(fields,row['text'])


if __name__=='__main__':unittest.main()
