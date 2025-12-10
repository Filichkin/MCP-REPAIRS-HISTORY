'''
Warranty Agent System - Multi-agent system for warranty claims analysis.

This package provides a LangGraph-based multi-agent system that analyzes
warranty claims, repair history, and compliance with consumer protection laws.
'''

__version__ = '0.1.0'
__author__ = 'Your Name'

from agent.graph import execute_query, execute_query_stream
from agent.api.app import app

__all__ = ['execute_query', 'execute_query_stream', 'app']
