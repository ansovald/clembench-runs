from check_scores_files import build_instance_dict, count_missing_scores


def _count_missing_scores(missing_scores):
    total = 0
    for model in missing_scores.values():
        for game in model.values():
            for experiment in game.values():
                total += len(experiment)
    return total


def test_count_missing_scores_v1_6_returns_zero():
    instance_dict, _ = build_instance_dict("v1.6")
    _, missing_scores = count_missing_scores("v1.6", instance_dict)
    missing_count = _count_missing_scores(missing_scores)
    assert missing_count == 0, f"There should be no 'scores.json' missing, but there are: {missing_count}"
