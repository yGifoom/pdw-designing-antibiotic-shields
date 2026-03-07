from pipeline.stage_registry import STAGE_ORDER, select_stage_window


def test_stage_window_selection() -> None:
    window = select_stage_window(STAGE_ORDER, "04_hotspot_detect", "07_design_seq_ligandmpnn")
    assert window[0] == "04_hotspot_detect"
    assert window[-1] == "07_design_seq_ligandmpnn"
    assert len(window) == 4
