import unittest
import re
from html.parser import HTMLParser

class SimpleDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = {}
        self.spans = {}
        self.selects = {}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        tag_id = attr_dict.get("id")
        if tag == "input" and tag_id:
            self.inputs[tag_id] = attr_dict
        elif tag == "span" and tag_id:
            self.spans[tag_id] = attr_dict
        elif tag == "select" and tag_id:
            self.selects[tag_id] = attr_dict

class TestResidentModalRestyling(unittest.TestCase):
    def setUp(self):
        with open("frontend/census.html", "r", encoding="utf-8") as f:
            self.html_content = f.read()
        self.parser = SimpleDOMParser()
        self.parser.feed(self.html_content)

    def test_modal_exists(self):
        self.assertIn('id="residentModal"', self.html_content)

    def test_contact_number_input_group(self):
        contact_input = self.parser.inputs.get("rf_contact")
        self.assertIsNotNone(contact_input, "rf_contact input must exist")
        self.assertEqual(contact_input.get("type"), "tel")
        self.assertEqual(contact_input.get("maxlength"), "10")
        self.assertEqual(contact_input.get("placeholder"), "9171234567")

        # Static +63 prefix markup
        self.assertIn("+63", self.html_content)
        match = re.search(r'<span[^>]*>\+63</span>.*?<input[^>]*id=["\']rf_contact["\']', self.html_content, re.DOTALL)
        self.assertIsNotNone(match, "Static +63 prefix must precede rf_contact input")
        self.assertIn("bg-[#edf5f0]", self.html_content)
        self.assertIn("border-[#c6dfd4]", self.html_content)
        self.assertIn("rounded-xl", self.html_content)

    def test_all_character_counters_present_with_limits(self):
        expected_counters = [
            ("rf_last", "rf_last_count", 50),
            ("rf_first", "rf_first_count", 50),
            ("rf_mid", "rf_mid_count", 50),
            ("rf_nat", "rf_nat_count", 50),
            ("rf_addr", "rf_addr_count", 150),
            ("rf_hh", "rf_hh_count", 20),
            ("rf_contact", "rf_contact_count", 10),
            ("rf_occ", "rf_occ_count", 50),
        ]

        for input_id, count_id, max_len in expected_counters:
            inp = self.parser.inputs.get(input_id)
            self.assertIsNotNone(inp, f"Input #{input_id} must exist")
            self.assertEqual(str(inp.get("maxlength")), str(max_len), f"Input #{input_id} maxlength must be {max_len}")

            count_span = self.parser.spans.get(count_id)
            self.assertIsNotNone(count_span, f"Counter #{count_id} must exist")
            cls = count_span.get("class", "")
            self.assertIn("text-xs", cls)
            self.assertIn("text-[#52796f]", cls)
            self.assertIn("text-right", cls)
            self.assertIn(f"0/{max_len}", self.html_content)

    def test_unaltered_fields(self):
        res_no = self.parser.inputs.get("rf_resNo")
        self.assertIsNotNone(res_no)
        self.assertIn("disabled", res_no)

        dob = self.parser.inputs.get("rf_dob")
        self.assertIsNotNone(dob)
        self.assertEqual(dob.get("type"), "date")
        self.assertIn("data-no-future", dob)

        for select_id in ["rf_sex", "rf_civil", "rf_zone", "rf_voter", "rf_status"]:
            sel = self.parser.selects.get(select_id)
            self.assertIsNotNone(sel, f"Dropdown #{select_id} must exist")

    def test_js_logic_functions(self):
        self.assertIn("function updateResidentCharCounters()", self.html_content)
        self.assertIn("function initResidentCharCounters()", self.html_content)
        self.assertIn("window.updateResidentCharCounters", self.html_content)
        self.assertIn("window.initResidentCharCounters", self.html_content)
        # Check stripping of prefix on edit
        self.assertIn("contactDigits.startsWith('63')", self.html_content)
        self.assertIn("contactDigits.startsWith('0')", self.html_content)

if __name__ == "__main__":
    unittest.main()
