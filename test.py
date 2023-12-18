
def test_valid(cldf_dataset, cldf_logger):
    clts_ids = [r['CLTS_ID'] for r in cldf_dataset['ParameterTable']]
    assert len(set(clts_ids)) == len(clts_ids)
    assert cldf_dataset.validate(log=cldf_logger)
