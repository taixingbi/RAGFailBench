from ragfailbench.io import read_jsonl, write_jsonl
from ragfailbench.validation.seed_filter import filter_seeds


def test_filter_seeds_moves_seed_and_derived_rows(tmp_path):
    final = tmp_path / "6_final"
    (final / "failures").mkdir(parents=True)
    write_jsonl(final / "clean_seeds.jsonl", [
        {"sample_id": "seed_000001", "question": "When did Ray Dolby die?"},
        {"sample_id": "seed_000002", "question": "When and where did Ray Dolby found Dolby Laboratories?"},
    ])
    cases = [
        {"failure_id": "seed_000001__conflict__low", "parent_seed_id": "seed_000001"},
        {"failure_id": "seed_000002__conflict__low", "parent_seed_id": "seed_000002"},
    ]
    write_jsonl(final / "failure_cases.jsonl", cases)
    write_jsonl(final / "failures" / "conflict.jsonl", cases)
    write_jsonl(final / "evaluation_results.jsonl", [
        {"sample_id": "seed_000001"},
        {"sample_id": "seed_000002__conflict__low__aware"},
        {"sample_id": "seed_000002__closed_book"},
    ])

    manifest = filter_seeds(final)

    assert manifest["excluded_seed_ids"] == ["seed_000002"]
    assert [r["sample_id"] for r in read_jsonl(final / "evaluation_results.jsonl")] == ["seed_000001"]
    assert len(list(read_jsonl(final / "failures" / "conflict.jsonl"))) == 1
    moved = final / "excluded_multi_part"
    assert len(list(read_jsonl(moved / "evaluation_results.jsonl"))) == 2
    assert len(list(read_jsonl(moved / "failures" / "conflict.jsonl"))) == 1
    # A second run changes nothing.
    assert filter_seeds(final)["excluded_seed_ids"] == []
    assert len(list(read_jsonl(moved / "evaluation_results.jsonl"))) == 2
