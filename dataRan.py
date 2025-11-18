"""
Test Data Generator - Entry Point

A tool for generating comprehensive test data in JSON format or directly to database.
Supports Khmer and English content generation with AI-powered realistic data.
"""

import flet as ft
from data_ran.ui.main_ui import DataGeneratorApp


def main(page: ft.Page):
    """Main entry point for the data generator application."""
    app = DataGeneratorApp(page)
    app.run()


if __name__ == "__main__":
    ft.app(target=main)

