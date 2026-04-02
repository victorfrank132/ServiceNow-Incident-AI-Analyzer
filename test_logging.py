#!/usr/bin/env python
"""Test LLM and incident state logging."""

import logging
from src.logging import setup_llm_analysis_logging

# Setup LLM logger
llm_logger = setup_llm_analysis_logging('logs/llm_analysis_test.log')

# Create test record with LLM data
record = logging.LogRecord(
    name='llm_analysis',
    level=logging.INFO,
    pathname='',
    lineno=0,
    msg='Test LLM Analysis',
    args=(),
    exc_info=None
)
record.incident_number = 'INC0001234'
record.llm_input = 'What is the root cause of this database issue?'
record.llm_output = '{"root_cause": "Database connection pool exhausted", "confidence": 85}'
record.confidence = 85

llm_logger.handle(record)
print('✓ LLM Logger test passed')

# Check the log file
import os
if os.path.exists('logs/llm_analysis_test.log'):
    with open('logs/llm_analysis_test.log', 'r') as f:
        content = f.read()
        print('✓ Log file created')
        print(f'Content preview: {content[:150]}...')
else:
    print('✗ Log file not created')
