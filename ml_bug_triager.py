# services/ml_bug_triager.py
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class MLBugTriager:
    """
    Machine Learning-based Bug Triaging System
    Uses historical bug data and developer profiles to assign bugs intelligently
    """
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english',
            min_df=2,
            max_df=0.85
        )
        
        self.severity_encoder = LabelEncoder()
        self.component_encoder = LabelEncoder()
        self.developer_encoder = LabelEncoder()
        
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model_dir = "models"
        self.is_trained = False
        self.developer_workload = {}
        self.developer_expertise = {}
        self.historical_performance = {}
        
        os.makedirs(self.model_dir, exist_ok=True)
    
    def extract_features_from_bug(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract comprehensive features from bug report
        Based on research: feature extraction is critical for ML performance
        """
        title = bug_data.get('title', '')
        description = bug_data.get('description', '')
        severity = bug_data.get('severity', 'Medium')
        component = bug_data.get('component', 'General')
        labels = bug_data.get('labels', '')
        stack_trace = bug_data.get('stack_trace', '')
        
        # Combine text features
        combined_text = f"{title} {description} {labels} {stack_trace}"
        
        # Extract technical keywords
        tech_keywords = self._extract_technical_keywords(combined_text)
        
        # Calculate complexity score
        complexity_score = self._calculate_bug_complexity(bug_data)
        
        return {
            'text': combined_text,
            'title': title,
            'description': description,
            'severity': severity,
            'component': component,
            'labels': labels,
            'tech_keywords': tech_keywords,
            'complexity_score': complexity_score,
            'text_length': len(combined_text),
            'has_stack_trace': len(stack_trace) > 0
        }
    
    def _extract_technical_keywords(self, text: str) -> List[str]:
        """Extract technical terms and technologies from bug text"""
        text_lower = text.lower()
        
        tech_patterns = {
            'languages': ['python', 'java', 'javascript', 'typescript', 'sql', 'c++', 'c#', 'ruby', 'php', 'go'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node', 'express', 'fastapi'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'concepts': ['api', 'rest', 'graphql', 'authentication', 'authorization', 'security', 'performance', 'memory', 'crash']
        }
        
        found_keywords = []
        for category, keywords in tech_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    def _calculate_bug_complexity(self, bug_data: Dict[str, Any]) -> float:
        """
        Calculate bug complexity score based on multiple factors
        Higher score = more complex bug
        """
        complexity = 0.0
        
        # Severity contribution
        severity_weights = {'Critical': 1.0, 'High': 0.75, 'Medium': 0.5, 'Low': 0.25}
        complexity += severity_weights.get(bug_data.get('severity', 'Medium'), 0.5)
        
        # Description length (longer = potentially more complex)
        desc_length = len(bug_data.get('description', ''))
        if desc_length > 500:
            complexity += 0.3
        elif desc_length > 200:
            complexity += 0.15
        
        # Has stack trace (indicates crash/error)
        if len(bug_data.get('stack_trace', '')) > 0:
            complexity += 0.2
        
        # Technical keywords count
        text = f"{bug_data.get('title', '')} {bug_data.get('description', '')}"
        tech_keywords = self._extract_technical_keywords(text)
        complexity += min(len(tech_keywords) * 0.1, 0.3)
        
        return min(complexity, 1.0)  # Normalize to 0-1
    
    def build_developer_profiles(self, developers: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """
        Build comprehensive developer profiles with expertise mapping
        """
        profiles = {}
        
        for dev in developers:
            name = dev.get('name', '')
            skills = dev.get('skills', '').lower()
            contributions = dev.get('contributions', '').lower()
            modules = dev.get('modules', [])
            
            # Extract expertise domains
            expertise_domains = []
            combined_text = f"{skills} {contributions}"
            
            # Technology expertise
            tech_keywords = self._extract_technical_keywords(combined_text)
            expertise_domains.extend(tech_keywords)
            
            # Module expertise
            expertise_domains.extend([m.lower() for m in modules])
            
            # Experience level (heuristic based on contributions)
            experience_level = 'senior' if 'several' in contributions or 'significantly' in contributions else 'mid'
            
            profiles[name] = {
                'name': name,
                'skills': skills,
                'modules': modules,
                'expertise_domains': list(set(expertise_domains)),
                'experience_level': experience_level,
                'current_workload': self.developer_workload.get(name, 0),
                'historical_performance': self.historical_performance.get(name, {'avg_resolution_time': 0, 'success_rate': 0.8})
            }
            
            self.developer_expertise[name] = profiles[name]
        
        return profiles
    
    def calculate_developer_scores(self, bug_features: Dict, developer_profiles: Dict) -> List[Tuple[str, float, str]]:
        """
        Calculate matching scores for all developers
        Returns: List of (developer_name, score, reason) tuples
        """
        scores = []
        
        bug_keywords = set(bug_features['tech_keywords'])
        bug_component = bug_features['component'].lower()
        bug_severity = bug_features['severity']
        bug_complexity = bug_features['complexity_score']
        
        for dev_name, profile in developer_profiles.items():
            score = 0.0
            reasons = []
            
            # 1. Expertise matching (40% weight)
            dev_expertise = set(profile['expertise_domains'])
            expertise_overlap = len(bug_keywords.intersection(dev_expertise))
            
            if expertise_overlap > 0:
                expertise_score = min(expertise_overlap / len(bug_keywords) if bug_keywords else 0, 1.0)
                score += expertise_score * 0.4
                matched_skills = list(bug_keywords.intersection(dev_expertise))[:3]
                if matched_skills:
                    reasons.append(f"Expertise: {', '.join(matched_skills)}")
            
            # 2. Module/Component matching (30% weight)
            if bug_component in [m.lower() for m in profile['modules']]:
                score += 0.3
                reasons.append(f"Module expert: {bug_features['component']}")
            
            # 3. Workload balancing (15% weight)
            current_load = profile['current_workload']
            max_load = 10  # Maximum concurrent bugs
            load_factor = 1.0 - (current_load / max_load)
            score += load_factor * 0.15
            
            if current_load < 3:
                reasons.append("Available capacity")
            
            # 4. Experience vs Complexity matching (10% weight)
            if bug_severity in ['Critical', 'High'] and profile['experience_level'] == 'senior':
                score += 0.1
                reasons.append("Senior dev for critical bug")
            elif bug_complexity < 0.5 and profile['experience_level'] == 'mid':
                score += 0.05
            
            # 5. Historical performance (5% weight)
            perf = profile['historical_performance']
            if perf['success_rate'] > 0.85:
                score += 0.05
                reasons.append("High success rate")
            
            # Normalize score to 0-1 range
            score = min(score, 1.0)
            
            # Convert to confidence percentage (30-95% range)
            confidence = 0.30 + (score * 0.65)
            
            reason_str = "; ".join(reasons) if reasons else "General assignment based on availability"
            
            scores.append((dev_name, confidence, reason_str))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores
    
    def assign_bug_to_developer(self, bug_data: Dict, developers: List[Dict]) -> Dict[str, Any]:
        """
        Main method: Assign bug to best developer using ML-based scoring
        """
        # Extract bug features
        bug_features = self.extract_features_from_bug(bug_data)
        
        # Build developer profiles
        developer_profiles = self.build_developer_profiles(developers)
        
        # Calculate scores for all developers
        developer_scores = self.calculate_developer_scores(bug_features, developer_profiles)
        
        if not developer_scores:
            return {
                'developer': 'Unassigned',
                'confidence': 0.30,
                'reason': 'No suitable developer found'
            }
        
        # Get best match
        best_developer, confidence, reason = developer_scores[0]
        
        # Update workload
        self.developer_workload[best_developer] = self.developer_workload.get(best_developer, 0) + 1
        
        # Log assignment
        logger.info(f"Bug '{bug_features['title'][:50]}' -> {best_developer} ({confidence*100:.0f}%)")
        logger.info(f"Reason: {reason}")
        logger.info(f"Top 3 candidates: {[(d, f'{c*100:.0f}%') for d, c, _ in developer_scores[:3]]}")
        
        return {
            'developer': best_developer,
            'confidence': round(confidence, 2),
            'reason': reason,
            'alternatives': [
                {'developer': d, 'confidence': round(c, 2), 'reason': r} 
                for d, c, r in developer_scores[1:4]
            ]
        }
    
    def train_ml_model(self, historical_data: List[Dict[str, Any]]):
        """
        Train ML model on historical bug assignment data
        For future enhancement when historical data is available
        """
        if len(historical_data) < 50:
            logger.warning("Insufficient historical data for ML training")
            return
        
        try:
            df = pd.DataFrame(historical_data)
            
            # Feature extraction
            X_text = self.tfidf_vectorizer.fit_transform(df['text'])
            X_severity = self.severity_encoder.fit_transform(df['severity'])
            X_component = self.component_encoder.fit_transform(df['component'])
            
            # Combine features
            X = np.hstack([
                X_text.toarray(),
                X_severity.reshape(-1, 1),
                X_component.reshape(-1, 1)
            ])
            
            # Target variable
            y = self.developer_encoder.fit_transform(df['assigned_developer'])
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.rf_model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.rf_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Model trained with accuracy: {accuracy:.2%}")
            logger.info(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
            
            # Save model
            self._save_model()
            self.is_trained = True
            
        except Exception as e:
            logger.error(f"Error training ML model: {str(e)}")
    
    def _save_model(self):
        """Save trained model components"""
        try:
            joblib.dump(self.rf_model, os.path.join(self.model_dir, "rf_classifier.joblib"))
            joblib.dump(self.tfidf_vectorizer, os.path.join(self.model_dir, "tfidf_vectorizer.joblib"))
            joblib.dump(self.developer_encoder, os.path.join(self.model_dir, "developer_encoder.joblib"))
            logger.info("ML model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def update_historical_performance(self, developer: str, resolution_time: float, success: bool):
        """
        Update developer performance metrics
        For continuous learning and improvement
        """
        if developer not in self.historical_performance:
            self.historical_performance[developer] = {
                'total_assignments': 0,
                'successful_assignments': 0,
                'total_resolution_time': 0,
                'avg_resolution_time': 0,
                'success_rate': 0.8
            }
        
        perf = self.historical_performance[developer]
        perf['total_assignments'] += 1
        perf['total_resolution_time'] += resolution_time
        
        if success:
            perf['successful_assignments'] += 1
        
        perf['avg_resolution_time'] = perf['total_resolution_time'] / perf['total_assignments']
        perf['success_rate'] = perf['successful_assignments'] / perf['total_assignments']