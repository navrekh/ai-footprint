from aifootprint_cli import __version__
from aifootprint_cli.cli import main


def test_help_exits_zero_and_lists_commands(capsys):
    exit_code = main(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    for command in ("event", "estimate", "usage", "compare", "benchmarks"):
        assert command in captured.out


def test_version_prints_the_single_source_of_truth_version(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert __version__ in captured.out


def test_no_command_prints_help_and_exits_zero(capsys):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out


def test_unknown_command_is_a_validation_exit_code(capsys):
    exit_code = main(["not-a-real-command"])
    assert exit_code == 2


def test_every_command_has_help(capsys):
    for command in ("event", "estimate", "usage", "compare", "benchmarks"):
        exit_code = main([command, "--help"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "usage:" in captured.out


def test_every_usage_subcommand_has_help(capsys):
    for sub in (
        "summary",
        "by-provider",
        "by-model",
        "by-activity",
        "by-application",
        "timeseries",
    ):
        exit_code = main(["usage", sub, "--help"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "usage:" in captured.out


def test_every_benchmarks_subcommand_has_help(capsys):
    exit_code = main(["benchmarks", "list", "--help"])
    assert exit_code == 0
    capsys.readouterr()

    exit_code = main(["benchmarks", "get", "--help"])
    assert exit_code == 0
    capsys.readouterr()

    exit_code = main(["benchmarks", "run", "--help"])
    assert exit_code == 0


def test_usage_without_subcommand_is_a_validation_error():
    exit_code = main(["usage"])
    assert exit_code == 2


def test_benchmarks_without_subcommand_is_a_validation_error():
    exit_code = main(["benchmarks"])
    assert exit_code == 2


def test_event_missing_required_argument_is_a_validation_error():
    exit_code = main(["event", "--provider", "openai"])
    assert exit_code == 2


def test_event_invalid_modality_choice_is_a_validation_error():
    exit_code = main(
        [
            "event",
            "--provider",
            "openai",
            "--model",
            "m",
            "--modality",
            "not-a-modality",
            "--activity-type",
            "text_generation",
        ]
    )
    assert exit_code == 2
