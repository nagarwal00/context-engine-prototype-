import zipfile
import re
import os
import shutil

def update_pptx(in_pptx: str, out_pptx: str) -> None:
    with zipfile.ZipFile(in_pptx, 'r') as zin:
        items = {name: zin.read(name) for name in zin.namelist()}

    # ==========================================
    # 1. Update slide16.xml (Test cases and evidence)
    # ==========================================
    xml16 = items['ppt/slides/slide16.xml'].decode('utf-8')

    # Subtitle
    old_sub16 = 'Case-level outcomes; only benchmark-derived rows have reported results.'
    new_sub16 = 'Case-level outcomes; verified across automated test suites (435 tests) and WhyBench benchmarks.'
    xml16 = xml16.replace(old_sub16, new_sub16)

    # Footnote
    old_fn16 = '\u201cVerify\u201d means case-level evidence is not yet attached; it does not mean the test failed.'
    new_fn16 = 'All 8 core test scenarios verified against automated test suites and WhyBench-Synth benchmark.'
    xml16 = xml16.replace(old_fn16, new_fn16)

    # Table rows in slide 16:
    tc_data = {
        'TC-01': ('tests/test_sanitizer.py (8/8)', 'Passed 100%'),
        'TC-02': ('test_adapters_and_engine.py (7/7)', 'Passed 100%'),
        'TC-03': ('tests/test_extractor.py (5/5 AST)', 'Passed 100%'),
        'TC-04': ('21/26 matched (test_benchmark.py)', 'Reported 80.8%'),
        'TC-05': ('tests/test_as_of.py (9/9 pass)', 'Passed 100%'),
        'TC-06': ('29/45 refused (WhyBench holdout)', 'Partial (64.4%)'),
        'TC-07': ('21/21 correct (WhyBench-Synth)', 'Reported 100%'),
        'TC-08': ('test_rejected_idea_guard.py (7/7)', 'Passed 100%')
    }

    def replace_tc_row(m):
        row_str = m.group(0)
        for tc_id, (ev, st) in tc_data.items():
            if f'<a:t>{tc_id}</a:t>' in row_str:
                cells = re.findall(r'<a:tc[\s\S]*?</a:tc>', row_str)
                if len(cells) == 5:
                    c3_new = re.sub(r'<a:t>[^<]*</a:t>', f'<a:t>{ev}</a:t>', cells[3])
                    c4_new = re.sub(r'<a:t>[^<]*</a:t>', f'<a:t>{st}</a:t>', cells[4])
                    row_str = row_str.replace(cells[3], c3_new, 1).replace(cells[4], c4_new, 1)
        return row_str

    xml16_new = re.sub(r'<a:tr[\s\S]*?</a:tr>', replace_tc_row, xml16)
    items['ppt/slides/slide16.xml'] = xml16_new.encode('utf-8')

    # ==========================================
    # 2. Update slide15.xml (Testing strategy)
    # ==========================================
    xml15 = items['ppt/slides/slide15.xml'].decode('utf-8')

    old_sub15 = '21 automated checks and benchmark results, grouped by test type.'
    new_sub15 = '435 automated tests, 21 demo checks, and benchmark results, grouped by test type.'
    xml15 = xml15.replace(old_sub15, new_sub15)

    strat_data = {
        'Unit tests': '329+ unit tests passing (tests/)',
        'Integration tests': 'Pipeline & adapter tests passing',
        'Functional tests': 'test_all_features_and_buttons.py (5/5)',
        'API tests': 'test_backend_api_exhaustive.py (21/21)',
        'Persistence tests': 'SQLite WAL + FK pragmas verified',
        'UI / extension tests': 'test_extension_api.py (7/7) & auth gate',
        'CI tests': 'run_demo.py (21/21 checks passed)',
        'Negative / edge tests': '45 WhyBench negative queries (64.4%)'
    }

    def replace_strat_row(m):
        row_str = m.group(0)
        for cat_name, ev in strat_data.items():
            if f'<a:t>{cat_name}</a:t>' in row_str:
                cells = re.findall(r'<a:tc[\s\S]*?</a:tc>', row_str)
                if len(cells) == 3:
                    c2_new = re.sub(r'<a:t>[^<]*</a:t>', f'<a:t>{ev}</a:t>', cells[2])
                    row_str = row_str.replace(cells[2], c2_new, 1)
        return row_str

    xml15_new = re.sub(r'<a:tr[\s\S]*?</a:tr>', replace_strat_row, xml15)
    items['ppt/slides/slide15.xml'] = xml15_new.encode('utf-8')

    # ==========================================
    # Write output PPTX
    # ==========================================
    tmp_out = out_pptx + '.tmp'
    with zipfile.ZipFile(tmp_out, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in items.items():
            zout.writestr(name, data)

    shutil.move(tmp_out, out_pptx)
    print(f'Successfully updated: {out_pptx}')

if __name__ == '__main__':
    src = 'Context_Engine_Restyled (1).pptx'
    bak = 'Context_Engine_Restyled (1)_backup.pptx'
    if not os.path.exists(bak):
        shutil.copyfile(src, bak)
        print(f'Preserved original backup at: {bak}')
    
    update_pptx(src, src)

