
import sys
from unittest.mock import MagicMock, patch
import unittest
import datetime

# Mock selenium to avoid ImportError
sys.modules["selenium"] = MagicMock()
sys.modules["selenium.webdriver"] = MagicMock()

# Mock reverie.backend_server.infra.llm to avoid further import issues
mock_llm = MagicMock()
sys.modules["reverie.backend_server.infra.llm"] = mock_llm

# Now we can import the module under test
from persona.cognitive_modules.reflector.legacy import LegacyReflector

class TestLegacyReflector(unittest.TestCase):
    def setUp(self):
        # Mock the Persona object
        self.mock_persona = MagicMock()
        self.mock_persona.scratch.name = "Test Persona"
        self.mock_persona.scratch.curr_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        self.mock_persona.scratch.importance_trigger_max = 100
        self.mock_persona.scratch.importance_trigger_curr = 100
        self.mock_persona.scratch.importance_ele_n = 0
        self.mock_persona.scratch.chatting_end_time = None
        
        # Mock associative memory
        self.mock_persona.a_mem.seq_event = []
        self.mock_persona.a_mem.seq_thought = []
        
        # Initialize the LegacyReflector with the mocked persona
        self.reflector = LegacyReflector(self.mock_persona)

    def test_reflection_trigger_false(self):
        """
        Test that _reflection_trigger returns False when importance_trigger_curr > 0.
        """
        self.mock_persona.scratch.importance_trigger_curr = 50
        self.assertFalse(self.reflector._reflection_trigger())

    def test_reflection_trigger_true(self):
        """
        Test that _reflection_trigger returns True when importance_trigger_curr <= 0
        and there are events or thoughts in memory.
        """
        self.mock_persona.scratch.importance_trigger_curr = 0
        # Add a dummy event to ensure the list is not empty
        self.mock_persona.a_mem.seq_event = [MagicMock()]
        self.assertTrue(self.reflector._reflection_trigger())

    def test_reflection_trigger_empty_memory(self):
        """
        Test that _reflection_trigger returns False even if importance_trigger_curr <= 0
        when memory is empty.
        """
        self.mock_persona.scratch.importance_trigger_curr = 0
        self.mock_persona.a_mem.seq_event = []
        self.mock_persona.a_mem.seq_thought = []
        self.assertFalse(self.reflector._reflection_trigger())

    def test_reset_reflection_counter(self):
        """
        Test that _reset_reflection_counter correctly resets the counters.
        """
        self.mock_persona.scratch.importance_trigger_curr = 0
        self.mock_persona.scratch.importance_ele_n = 10
        
        self.reflector._reset_reflection_counter()
        
        self.assertEqual(self.mock_persona.scratch.importance_trigger_curr, 100)
        self.assertEqual(self.mock_persona.scratch.importance_ele_n, 0)

    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_focal_pt')
    def test_generate_focal_points(self, mock_run_gpt):
        """
        Test _generate_focal_points calls the GPT prompt correctly.
        """
        # Setup mock nodes
        mock_node1 = MagicMock()
        mock_node1.last_accessed = datetime.datetime(2023, 1, 1, 10, 0, 0)
        mock_node1.embedding_key = "Event 1"
        
        mock_node2 = MagicMock()
        mock_node2.last_accessed = datetime.datetime(2023, 1, 1, 11, 0, 0)
        mock_node2.embedding_key = "Event 2"
        
        self.mock_persona.a_mem.seq_event = [mock_node1, mock_node2]
        self.mock_persona.scratch.importance_ele_n = 2
        
        # Mock GPT response
        mock_run_gpt.return_value = (["Focal Point 1", "Focal Point 2"], "debug_info")
        
        focal_points = self.reflector._generate_focal_points(2)
        
        self.assertEqual(focal_points, ["Focal Point 1", "Focal Point 2"])
        mock_run_gpt.assert_called_once()

    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_insight_and_guidance')
    def test_generate_insights_and_evidence(self, mock_run_gpt):
        """
        Test _generate_insights_and_evidence processes nodes and GPT response correctly.
        """
        # Setup mock nodes
        mock_node1 = MagicMock()
        mock_node1.embedding_key = "Node 1"
        mock_node1.node_id = "id_1"
        
        mock_node2 = MagicMock()
        mock_node2.embedding_key = "Node 2"
        mock_node2.node_id = "id_2"
        
        nodes = [mock_node1, mock_node2]
        
        # Mock GPT response: Dictionary mapping thought to list of evidence indices
        mock_run_gpt.return_value = ({"Insight 1": [0], "Insight 2": [1]}, "debug_info")
        
        insights = self.reflector._generate_insights_and_evidence(nodes, 2)
        
        # Verify that indices were converted to node_ids
        expected_insights = {"Insight 1": ["id_1"], "Insight 2": ["id_2"]}
        self.assertEqual(insights, expected_insights)

    @patch('persona.cognitive_modules.reflector.legacy.get_embedding')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_event_poignancy')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_event_triple')
    def test_run_reflect(self, mock_triple, mock_poignancy, mock_embedding):
        """
        Test the full _run_reflect flow.
        """
        # Mock internal methods to isolate _run_reflect logic
        self.reflector._generate_focal_points = MagicMock(return_value=["Focal Point"])
        
        mock_node = MagicMock()
        mock_node.embedding_key = "Node Key"
        self.mock_persona.retriever.retrieve_weighted.return_value = {"Focal Point": [mock_node]}
        
        self.reflector._generate_insights_and_evidence = MagicMock(return_value={"New Thought": ["evidence_id"]})
        
        # Mock GPT and embedding responses
        mock_triple.return_value = (("Subject", "Predicate", "Object"), "debug")
        mock_poignancy.return_value = (5, "debug")
        mock_embedding.return_value = [0.1, 0.2, 0.3]
        
        self.reflector._run_reflect()
        
        # Verify that a thought was added to memory
        self.mock_persona.a_mem.add_thought.assert_called_once()
        args, _ = self.mock_persona.a_mem.add_thought.call_args
        
        # Check arguments passed to add_thought
        # (created, expiration, s, p, o, thought, keywords, thought_poignancy, thought_embedding_pair, evidence)
        self.assertEqual(args[5], "New Thought")
        self.assertEqual(args[9], ["evidence_id"])

    @patch('persona.cognitive_modules.reflector.legacy.get_embedding')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_memo_on_convo')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_planning_thought_on_convo')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_chat_poignancy')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_event_poignancy')
    @patch('persona.cognitive_modules.reflector.legacy.run_gpt_prompt_event_triple')
    def test_reflect_chat_end(self, mock_triple, mock_event_poig, mock_chat_poig, mock_planning, mock_memo, mock_embedding):
        """
        Test reflect method when a chat has just ended.
        """
        # Setup chat end condition
        curr_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        self.mock_persona.scratch.curr_time = curr_time
        # Chat ends 10 minutes from now? Wait, let's check the code.
        # if self.persona.scratch.curr_time + datetime.timedelta(0,10) == self.persona.scratch.chatting_end_time:
        # This implies checking if we are 10 seconds? or minutes? before end time?
        # datetime.timedelta(0, 10) is 10 seconds.
        
        self.mock_persona.scratch.chatting_end_time = curr_time + datetime.timedelta(seconds=10)
        self.mock_persona.scratch.chat = [["User", "Hello"], ["Agent", "Hi"]]
        self.mock_persona.scratch.chatting_with = "Other Agent"
        
        # Mock last chat node
        mock_chat_node = MagicMock()
        mock_chat_node.node_id = "chat_node_id"
        self.mock_persona.a_mem.get_last_chat.return_value = mock_chat_node
        
        # Mock GPT responses
        mock_planning.return_value = ("Planning thought", "debug")
        mock_memo.return_value = ("Memo thought", "debug")
        mock_triple.return_value = (("S", "P", "O"), "debug")
        mock_event_poig.return_value = (5, "debug") # For thought poignancy
        mock_embedding.return_value = [0.1]
        
        # Ensure reflection trigger is false so we only test the chat part
        self.reflector._reflection_trigger = MagicMock(return_value=False)
        
        self.reflector.reflect()
        
        # Should add two thoughts: one for planning, one for memo
        self.assertEqual(self.mock_persona.a_mem.add_thought.call_count, 2)

if __name__ == '__main__':
    unittest.main()
