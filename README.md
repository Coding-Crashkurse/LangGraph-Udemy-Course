# LangGraph-Udemy-Course

This repository contains a collection of Jupyter notebooks and supporting projects showcasing the functionality of **LangGraph**, a Python library for building and managing agents with graph-based workflows.

## Notebooks

- **00_TypedDict.ipynb**
  Explanation of the differences between `TypedDict` and Pydantic for managing state.

- **01_Basics.ipynb**
  Introduction to the basic concepts of LangGraph, including how to build simple agent workflows.

- **02_Tool_calling_basics.ipynb**
  Demonstrates how to enable agents to call tools effectively within LangChain (not LangGraph!).

- **03_Agent_basics.ipynb**
  Explores the fundamental features of creating and managing agents using LangGraph.

- **04_RAG_Basics.ipynb**
  Overview of Retrieval-Augmented Generation (RAG) basics with LangGraph.

- **05_RAG_Agent.ipynb**
  Implementation of an agent that leverages RAG for enhanced information retrieval.

- **06_RAG_Agent_with_memory.ipynb**
  Shows how to extend a RAG agent with memory capabilities for contextual responses.

- **07_Advanced_State.ipynb**
  Advanced techniques for managing agent states within LangGraph workflows.

- **08_Human_in_the_Loop.ipynb**
  Incorporates human input into LangGraph workflows for guided decision-making.

- **09_ParallelExecution.ipynb**
  Demonstrates parallel execution of nodes in LangGraph for efficient processing.

- **10_AsyncAndStreaming.ipynb**
  Explores asynchronous execution and streaming outputs in LangGraph workflows.

- **11_Subgraphs.ipynb**
  Illustrates how to use subgraphs to modularize and reuse parts of a workflow.

- **12_Agent_Patterns.ipynb**
  Showcases common agent design patterns and reusable templates.

- **13_LongTermMemory.ipynb**
  Implements long-term memory functionality in agents using LangGraph.

- **14_Durability_Memory.ipynb**
  Covers durable memory patterns for long-lived LangGraph applications.

## Additional Content

### scripts

**Description**: Supporting Python scripts used alongside the notebooks.

- **00_typeddict_with_mypy.py**: TypedDict example with type checking.

### unit_tests

**Description**: Demonstrates how to test LangGraph apps effectively.

- Includes examples of unit tests for LangGraph nodes.

### fullstackapp

**Description**: Capstone project demonstrating the integration of a full-stack application with a human-in-the-loop workflow.

- **Frontend**: Built with Angular.
- **Backend**: Built with FastAPI (async!).
- **Database**: PostgreSQL.
