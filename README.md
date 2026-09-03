# 🤖 CCA AI Assistant — University Handbook RAG System

[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20v4-38bdf8)](https://tailwindcss.com/)

An intelligent Retrieval-Augmented Generation (RAG) assistant designed to ingest university handbooks and answer student inquiries with precise page-level citations. Built with FastAPI, LangChain/FAISS vector embeddings, and a React/Vite dashboard interface.

---

## 📌 Table of Contents
- [Overview](#-overview)
- [Architecture](#️-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [License](#-license)

---

## 📖 Overview

Navigating lengthy university handbooks can be time-consuming for students and staff. **CCA AI Assistant** streamlines document search by:
- **Ingesting PDFs**: Extracting and chunking university policy documents into searchable vector embeddings.
- **Semantic Search**: Retrieving relevant document sections using vector similarity search.
- **Precise Citations**: Citing exact page numbers (`Page X`) alongside generated answers for easy verification.
- **Interactive UI**: Providing a responsive dark-mode chat and upload interface.

---

## 🏗️ Architecture

The system uses a two-tier architecture connecting a React frontend to a FastAPI RAG backend:

```text
  ┌────────────────────────┐         POST /ask          ┌────────────────────────┐
  │  React / Vite Frontend │ ─────────────────────────> │    FastAPI Backend     │
  │  (Tailwind CSS v4)     │ <───────────────────────── │   (RAG / Vector DB)    │
  └────────────────────────┘      Answer + Citations    └────────────────────────┘
---
# 🤖 CCA AI Assistant — University Handbook RAG System

[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20v4-38bdf8)](https://tailwindcss.com/)

An intelligent Retrieval-Augmented Generation (RAG) assistant designed to ingest university handbooks and answer student inquiries with precise page-level citations. Built with FastAPI, LangChain/FAISS vector embeddings, and a React/Vite dashboard interface.

---

## 📌 Table of Contents
- [Overview](#-overview)
- [Architecture](#️-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [License](#-license)

---

## 📖 Overview

Navigating lengthy university handbooks can be time-consuming for students and staff. **CCA AI Assistant** streamlines document search by:
- **Ingesting PDFs**: Extracting and chunking university policy documents into searchable vector embeddings.
- **Semantic Search**: Retrieving relevant document sections using vector similarity search.
- **Precise Citations**: Citing exact page numbers (`Page X`) alongside generated answers for easy verification.
- **Interactive UI**: Providing a responsive dark-mode chat and upload interface.

---

## 🏗️ Architecture

The system uses a two-tier architecture connecting a React frontend to a FastAPI RAG backend:

```text
  ┌────────────────────────┐         POST /ask          ┌────────────────────────┐
  │  React / Vite Frontend │ ─────────────────────────> │    FastAPI Backend     │
  │  (Tailwind CSS v4)     │ <───────────────────────── │   (RAG / Vector DB)    │
  └────────────────────────┘      Answer + Citations    └────────────────────────┘
