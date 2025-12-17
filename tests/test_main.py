import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import load_state, save_state, process_evaluations


class TestStateManagement:
    """Tests pour la gestion de l'état (fichier JSON)."""
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"eval1": "15.0", "eval2": null}')
    @patch('os.path.exists', return_value=True)
    def test_load_state_existing_file(self, mock_exists, mock_file):
        """Vérifie le chargement d'un fichier d'état existant."""
        state = load_state()
        
        assert state == {"eval1": "15.0", "eval2": None}
        mock_exists.assert_called_once()
    
    @patch('os.path.exists', return_value=False)
    def test_load_state_no_file(self, mock_exists):
        """Vérifie que load_state retourne un dict vide si pas de fichier."""
        state = load_state()
        
        assert state == {}
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('os.path.exists', return_value=True)
    def test_load_state_invalid_json(self, mock_exists, mock_file):
        """Vérifie la gestion d'un fichier JSON invalide."""
        state = load_state()
        
        assert state == {}
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_state(self, mock_file):
        """Vérifie la sauvegarde de l'état."""
        state = {"eval1": "15.0", "eval2": None}
        save_state(state)
        
        mock_file.assert_called_once_with("scodoc_state.json", "w")
        handle = mock_file()
        # Vérifier que json.dump a été appelé
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        assert "eval1" in written_content


class TestProcessEvaluations:
    """Tests pour la logique de traitement des évaluations."""
    
    def test_process_evaluations_new_evaluation_with_grade(self):
        """Vérifie la détection d'une nouvelle évaluation avec note."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': '15.5',
                        'moy': '12.0',
                        'min': '5.0',
                        'max': '19.0'
                    }
                }
            ]
        }
        
        state = {}
        notifier = Mock()
        
        process_evaluations(
            resource_dict, 
            "R1.01", 
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Vérifier que la notification a été envoyée
        assert notifier.notify_new_grade.called
        # Vérifier que l'état a été mis à jour
        assert state['eval1'] == '15.5'
    
    def test_process_evaluations_new_evaluation_without_grade(self):
        """Vérifie qu'une nouvelle évaluation sans note n'envoie pas de notification."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': None
                    }
                }
            ]
        }
        
        state = {}
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Pas de notification
        assert not notifier.notify_new_grade.called
        # Mais l'état est quand même mis à jour
        assert 'eval1' in state
        assert state['eval1'] is None
    
    def test_process_evaluations_grade_added(self):
        """Vérifie la détection d'une note ajoutée à une évaluation existante."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': '15.5',
                        'moy': '12.0',
                        'min': '5.0',
                        'max': '19.0'
                    }
                }
            ]
        }
        
        state = {'eval1': None}  # Évaluation existante sans note
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Vérifier que la notification a été envoyée
        assert notifier.notify_new_grade.called
        # Vérifier que l'état a été mis à jour
        assert state['eval1'] == '15.5'
    
    def test_process_evaluations_grade_updated(self):
        """Vérifie la détection d'une modification de note."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': '16.0',
                        'moy': '12.0'
                    }
                }
            ]
        }
        
        state = {'eval1': '15.0'}  # Note précédente
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Vérifier que la notification de mise à jour a été envoyée
        assert notifier.notify_grade_update.called
        # Vérifier que l'état a été mis à jour
        assert state['eval1'] == '16.0'
    
    def test_process_evaluations_placeholder_ignored(self):
        """Vérifie que les notes en attente (~) ne génèrent pas de notification."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': '~'
                    }
                }
            ]
        }
        
        state = {}
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Pas de notification pour un placeholder
        assert not notifier.notify_new_grade.called
        # État mis à jour avec le placeholder
        assert state['eval1'] == '~'
    
    def test_process_evaluations_placeholder_to_grade(self):
        """Vérifie la transformation d'un placeholder en note réelle."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': '15.5',
                        'moy': '12.0',
                        'min': '5.0',
                        'max': '19.0'
                    }
                }
            ]
        }
        
        state = {'eval1': '~'}  # Était en attente
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Doit notifier comme une nouvelle note
        assert notifier.notify_new_grade.called
        assert state['eval1'] == '15.5'
    
    def test_process_evaluations_initialization_no_mention(self):
        """Vérifie que l'initialisation ne mentionne pas @everyone."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': '15.5',
                        'moy': '12.0'
                    }
                }
            ]
        }
        
        state = {}
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=True  # Initialisation
        )
        
        # Vérifier que mention_everyone est False
        if notifier.notify_new_grade.called:
            call_kwargs = notifier.notify_new_grade.call_args[1]
            assert call_kwargs.get('mention_everyone') is False
    
    def test_process_evaluations_empty_list(self):
        """Vérifie le traitement d'une ressource sans évaluations."""
        resource_dict = {
            'evaluations': []
        }
        
        state = {}
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Aucune notification
        assert not notifier.notify_new_grade.called
        assert not notifier.notify_grade_update.called
        # État inchangé
        assert state == {}
    
    def test_process_evaluations_grade_removed(self):
        """Vérifie la détection d'une note supprimée."""
        resource_dict = {
            'evaluations': [
                {
                    'id': 'eval1',
                    'description': 'TP1',
                    'note': {
                        'value': None
                    }
                }
            ]
        }
        
        state = {'eval1': '15.0'}  # Avait une note
        notifier = Mock()
        
        process_evaluations(
            resource_dict,
            "R1.01",
            "Initiation au développement",
            state,
            notifier,
            is_initialization=False
        )
        
        # Notification de suppression
        assert notifier.notify_grade_update.called
        assert state['eval1'] is None
