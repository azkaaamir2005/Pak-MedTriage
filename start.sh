#!/bin/bash
python -m uvicorn app.main:app --reload --port 8000 &
python -m streamlit run app.py