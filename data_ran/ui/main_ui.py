"""
Main UI for data generator application.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import flet as ft
from config.app_config import app_config
from data_ran.pattern.registry import FeatureRegistry
from data_ran.pattern.orchestrator import DataGeneratorOrchestrator
from data_ran.script.db_dumper import DatabaseDumper
from data_ran.script.generators.group_generator import GroupGenerator
from data_ran.script.generators.user_generator import UserGenerator
from data_ran.script.generators.message_generator import MessageGenerator
from data_ran.script.generators.reaction_generator import ReactionGenerator
from data_ran.script.generators.media_generator import MediaGenerator
from data_ran.script.generators.tag_generator import TagGenerator
from data_ran.script.generators.deleted_generator import DeletedGenerator
from data_ran.script.generators.settings_generator import SettingsGenerator

logger = logging.getLogger(__name__)


class DataGeneratorApp:
    """Main application UI for data generator."""
    
    def __init__(self, page: ft.Page, db_path: Optional[str] = None):
        """Initialize the application."""
        self.page = page
        self.page.title = "Test Data Generator"
        self.page.window.width = 900
        self.page.window.height = 800
        self.page.scroll = ft.ScrollMode.AUTO
        self.db_path = db_path  # Store db_path for use in database dumper
        
        # Initialize registry and orchestrator
        self.registry = FeatureRegistry()
        self._register_generators()
        self.orchestrator = DataGeneratorOrchestrator(self.registry)
        
        # UI components
        self.date_range_type = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="year", label="1 Year"),
                ft.Radio(value="month", label="1 Month"),
                ft.Radio(value="custom", label="Custom Range")
            ]),
            value="month"
        )
        
        self.start_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime.now()
        )
        self.end_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime.now()
        )
        self.start_date_btn = ft.ElevatedButton(
            "Select Start Date",
            on_click=lambda _: self.start_date_picker.pick_date(),
            visible=False
        )
        self.end_date_btn = ft.ElevatedButton(
            "Select End Date",
            on_click=lambda _: self.end_date_picker.pick_date(),
            visible=False
        )
        
        # Feature checkboxes
        self.feature_checkboxes = {
            'groups': ft.Checkbox(label="Groups", value=True),
            'users': ft.Checkbox(label="Users", value=True),
            'messages': ft.Checkbox(label="Messages", value=True),
            'reactions': ft.Checkbox(label="Reactions", value=True),
            'media': ft.Checkbox(label="Media Files", value=True),
            'tags': ft.Checkbox(label="Tags", value=True),
            'deleted': ft.Checkbox(label="Deleted Items", value=True),
            'settings': ft.Checkbox(label="App Settings", value=False)
        }
        
        # Language selection
        self.language_checkboxes = {
            'khmer': ft.Checkbox(label="Khmer", value=True),
            'english': ft.Checkbox(label="English", value=True)
        }
        
        # Configuration inputs
        self.num_groups_input = ft.TextField(label="Number of Groups", value="3", width=200)
        self.num_groups_random = ft.Checkbox(label="Use Random Range", value=False)
        self.num_groups_min = ft.TextField(label="Min", value="2", width=100, visible=False)
        self.num_groups_max = ft.TextField(label="Max", value="5", width=100, visible=False)
        
        self.num_users_input = ft.TextField(label="Number of Users", value="10", width=200)
        
        self.messages_per_group_input = ft.TextField(label="Messages per Group", value="100", width=200)
        self.messages_random = ft.Checkbox(label="Use Random Range", value=False)
        self.messages_min = ft.TextField(label="Min", value="50", width=100, visible=False)
        self.messages_max = ft.TextField(label="Max", value="200", width=100, visible=False)
        
        self.reactions_min = ft.TextField(label="Min Reactions", value="0", width=100)
        self.reactions_max = ft.TextField(label="Max Reactions", value="5", width=100)
        
        self.media_percentage = ft.TextField(label="Media Percentage", value="30", width=200)
        
        self.tags_min = ft.TextField(label="Min Tags", value="0", width=100)
        self.tags_max = ft.TextField(label="Max Tags", value="3", width=100)
        
        self.deleted_percentage = ft.TextField(label="Deleted Items %", value="5", width=200)
        
        # Output options
        # Hide JSON option in production mode (only show in sample_db mode)
        is_sample_mode = app_config.is_sample_db_mode()
        self.output_json = ft.Checkbox(label="Generate JSON File", value=True, visible=is_sample_mode)
        self.output_db = ft.Checkbox(label="Direct Database Dump", value=False)
        self.db_path_input = ft.TextField(label="Database Path", value="./data/app.db", width=300)
        self.clear_db_first = ft.Checkbox(label="Clear Database First", value=False)
        
        # Progress and status
        self.progress_bar = ft.ProgressBar(width=400, visible=False)
        self.status_text = ft.Text("Ready", size=12)
        
        # Generate button
        self.generate_btn = ft.ElevatedButton(
            "Generate Data",
            on_click=self._on_generate_click,
            width=200
        )
        
        # Build UI
        self._build_ui()
    
    def _register_generators(self):
        """Register all generators with the registry."""
        self.registry.register('groups', GroupGenerator)
        self.registry.register('users', UserGenerator)
        self.registry.register('messages', MessageGenerator)
        self.registry.register('reactions', ReactionGenerator)
        self.registry.register('media', MediaGenerator)
        self.registry.register('tags', TagGenerator)
        self.registry.register('deleted', DeletedGenerator)
        self.registry.register('settings', SettingsGenerator)
    
    def _build_ui(self):
        """Build the UI layout."""
        # Date range section
        date_section = ft.Container(
            content=ft.Column([
                ft.Text("Date Range", size=16, weight=ft.FontWeight.BOLD),
                self.date_range_type,
                ft.Row([
                    self.start_date_btn,
                    self.end_date_btn
                ]),
                ft.Row([
                    ft.Text("Start:", visible=False),
                    ft.Text("End:", visible=False)
                ], visible=False)
            ]),
            padding=10
        )
        
        # Feature selection
        feature_section = ft.Container(
            content=ft.Column([
                ft.Text("Features", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([cb for cb in self.feature_checkboxes.values()], wrap=True)
            ]),
            padding=10
        )
        
        # Language selection
        language_section = ft.Container(
            content=ft.Column([
                ft.Text("Languages", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([cb for cb in self.language_checkboxes.values()])
            ]),
            padding=10
        )
        
        # Configuration section
        config_section = ft.Container(
            content=ft.Column([
                ft.Text("Configuration", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.num_groups_input,
                    self.num_groups_random
                ]),
                ft.Row([
                    self.num_groups_min,
                    self.num_groups_max
                ], visible=False),
                ft.Row([self.num_users_input]),
                ft.Row([
                    self.messages_per_group_input,
                    self.messages_random
                ]),
                ft.Row([
                    self.messages_min,
                    self.messages_max
                ], visible=False),
                ft.Row([
                    self.reactions_min,
                    self.reactions_max
                ]),
                ft.Row([self.media_percentage]),
                ft.Row([
                    self.tags_min,
                    self.tags_max
                ]),
                ft.Row([self.deleted_percentage])
            ]),
            padding=10
        )
        
        # Output options
        output_section = ft.Container(
            content=ft.Column([
                ft.Text("Output Options", size=16, weight=ft.FontWeight.BOLD),
                self.output_json,
                self.output_db,
                self.db_path_input,
                self.clear_db_first
            ]),
            padding=10
        )
        
        # Add date pickers to overlay
        self.page.overlay.extend([self.start_date_picker, self.end_date_picker])
        
        # Main layout with scrollable container
        main_content = ft.Container(
            content=ft.Column([
                ft.Text("Test Data Generator", size=24, weight=ft.FontWeight.BOLD),
                date_section,
                feature_section,
                language_section,
                config_section,
                output_section,
                ft.Row([
                    self.generate_btn,
                    self.progress_bar
                ]),
                self.status_text
            ], 
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=10
            ),
            expand=True,
            padding=10
        )
        
        self.page.add(main_content)
        
        # Set up event handlers
        self.num_groups_random.on_change = lambda e: self._toggle_random_range('groups', e.control.value)
        self.messages_random.on_change = lambda e: self._toggle_random_range('messages', e.control.value)
        self.date_range_type.on_change = lambda e: self._on_date_range_change(e.control.value)
    
    def _toggle_random_range(self, field: str, enabled: bool):
        """Toggle visibility of random range inputs."""
        if field == 'groups':
            self.num_groups_min.visible = enabled
            self.num_groups_max.visible = enabled
        elif field == 'messages':
            self.messages_min.visible = enabled
            self.messages_max.visible = enabled
        self.page.update()
    
    def _on_date_range_change(self, value: str):
        """Handle date range type change."""
        if value == "custom":
            self.start_date_btn.visible = True
            self.end_date_btn.visible = True
        else:
            self.start_date_btn.visible = False
            self.end_date_btn.visible = False
        self.page.update()
    
    def _get_date_range(self) -> dict:
        """Get date range based on selection."""
        range_type = self.date_range_type.value
        now = datetime.now()
        
        if range_type == "year":
            start = now - timedelta(days=365)
            end = now
        elif range_type == "month":
            start = now - timedelta(days=30)
            end = now
        else:  # custom
            start_val = self.start_date_picker.value
            end_val = self.end_date_picker.value
            
            if start_val:
                if isinstance(start_val, datetime):
                    start = start_val
                else:
                    start = datetime.combine(start_val, datetime.min.time())
            else:
                start = now - timedelta(days=30)
            
            if end_val:
                if isinstance(end_val, datetime):
                    end = end_val
                else:
                    end = datetime.combine(end_val, datetime.max.time())
            else:
                end = now
        
        return {'start': start, 'end': end}
    
    def _on_generate_click(self, e):
        """Handle generate button click."""
        try:
            # Disable button and show progress
            self.generate_btn.disabled = True
            self.progress_bar.visible = True
            self.status_text.value = "Generating data..."
            self.page.update()
            
            # Get configuration
            config = self._get_config()
            
            # Enable selected features
            for feature_name, checkbox in self.feature_checkboxes.items():
                if checkbox.value:
                    self.registry.enable_feature(feature_name)
                else:
                    self.registry.disable_feature(feature_name)
            
            # Generate data
            self.status_text.value = "Generating data..."
            self.page.update()
            
            data = self.orchestrator.generate(config)
            
            # Save JSON if requested (only in sample_db mode)
            if self.output_json.visible and self.output_json.value:
                self.status_text.value = "Saving JSON file..."
                self.page.update()
                self._save_json(data)
            
            # Dump to database if requested
            if self.output_db.value:
                self.status_text.value = "Dumping to database..."
                self.page.update()
                self._dump_to_database(data, config)
            
            self.status_text.value = "Generation completed successfully!"
            self.progress_bar.visible = False
            self.generate_btn.disabled = False
            self.page.update()
            
        except Exception as ex:
            logger.error(f"Error generating data: {ex}", exc_info=True)
            self.status_text.value = f"Error: {str(ex)}"
            self.progress_bar.visible = False
            self.generate_btn.disabled = False
            self.page.update()
    
    def _get_config(self) -> dict:
        """Get configuration from UI inputs."""
        # Get languages
        languages = []
        if self.language_checkboxes['khmer'].value:
            languages.append('khmer')
        if self.language_checkboxes['english'].value:
            languages.append('english')
        if not languages:
            languages = ['english']  # Default
        
        # Get messages per group
        if self.messages_random.value:
            messages_per_group = {
                'min': int(self.messages_min.value or 50),
                'max': int(self.messages_max.value or 200)
            }
        else:
            messages_per_group = int(self.messages_per_group_input.value or 100)
        
        # Get num groups
        if self.num_groups_random.value:
            num_groups = {
                'min': int(self.num_groups_min.value or 2),
                'max': int(self.num_groups_max.value or 5)
            }
        else:
            num_groups = int(self.num_groups_input.value or 3)
        
        config = {
            'date_range': self._get_date_range(),
            'languages': languages,
            'num_groups': num_groups,
            'num_users': int(self.num_users_input.value or 10),
            'messages_per_group': messages_per_group,
            'reactions_per_message': {
                'min': int(self.reactions_min.value or 0),
                'max': int(self.reactions_max.value or 5)
            },
            'media_percentage': int(self.media_percentage.value or 30),
            'tag_config': {
                'min_tags': int(self.tags_min.value or 0),
                'max_tags': int(self.tags_max.value or 3)
            },
            'deleted_percentage': int(self.deleted_percentage.value or 5)
        }
        
        return config
    
    def _save_json(self, data: dict):
        """Save generated data to JSON file."""
        # Open file picker
        file_picker = ft.FilePicker(
            on_result=lambda e: self._save_json_file(e.path, data) if e.path else None
        )
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.save_file(
            dialog_title="Save JSON File",
            file_name=f"test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"]
        )
    
    def _save_json_file(self, path: str, data: dict):
        """Save JSON file to specified path."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            self.status_text.value = f"JSON saved to {path}"
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            self.status_text.value = f"Error saving JSON: {str(e)}"
    
    def _dump_to_database(self, data: dict, config: dict):
        """Dump data directly to database."""
        try:
            # Use provided db_path if available, otherwise use input field value
            db_path = self.db_path or self.db_path_input.value or "./data/app.db"
            # Update input field to show the path being used
            if self.db_path:
                self.db_path_input.value = self.db_path
            dumper = DatabaseDumper(db_path)
            
            clear_first = self.clear_db_first.value
            
            success = dumper.dump_data(data, clear_first=clear_first)
            
            if success:
                self.status_text.value = f"Data dumped to database: {db_path}"
            else:
                self.status_text.value = "Error dumping to database"
        except Exception as e:
            logger.error(f"Error dumping to database: {e}")
            self.status_text.value = f"Error: {str(e)}"
    
    def run(self):
        """Run the application."""
        pass  # Already added to page in _build_ui

