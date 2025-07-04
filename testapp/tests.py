# testapp/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Subject, SubjectDay, Question, Test, TestQuestion, Result, StudentAnswer
import json

class SubjectModelTest(TestCase):
    """Test Subject model functionality"""
    
    def setUp(self):
        self.subject = Subject.objects.create(
            name="Mathematics",
            grade=9,
            start_time="10:00",
            questions_count=20
        )
        SubjectDay.objects.create(subject=self.subject, day_of_week=1)  # Monday
        
    def test_subject_creation(self):
        """Test subject creation"""
        self.assertEqual(self.subject.name, "Mathematics")
        self.assertEqual(self.subject.grade, 9)
        self.assertEqual(self.subject.questions_count, 20)
    
    def test_has_enough_questions(self):
        """Test has_enough_questions method"""
        # Initially no questions
        self.assertFalse(self.subject.has_enough_questions())
        
        # Add enough questions
        for i in range(20):
            Question.objects.create(
                subject=self.subject,
                question_text=f"Question {i+1}",
                option_a="Option A",
                option_b="Option B", 
                option_c="Option C",
                option_d="Option D",
                correct_answer="A"
            )
        
        self.assertTrue(self.subject.has_enough_questions())
    
    def test_get_scheduled_days(self):
        """Test get_scheduled_days method"""
        days = self.subject.get_scheduled_days()
        self.assertEqual(days.count(), 1)
        self.assertEqual(days.first().day_of_week, 1)


class QuestionModelTest(TestCase):
    """Test Question model functionality"""
    
    def setUp(self):
        self.subject = Subject.objects.create(
            name="Science",
            grade=8,
            start_time="11:00",
            questions_count=15
        )
        
        self.question = Question.objects.create(
            subject=self.subject,
            question_text="What is the capital of France?",
            option_a="London",
            option_b="Paris",
            option_c="Berlin", 
            option_d="Madrid",
            correct_answer="B"
        )
    
    def test_question_creation(self):
        """Test question creation"""
        self.assertEqual(self.question.subject, self.subject)
        self.assertEqual(self.question.correct_answer, "B")
    
    def test_get_options(self):
        """Test get_options method"""
        options = self.question.get_options()
        expected_options = {
            'A': 'London',
            'B': 'Paris', 
            'C': 'Berlin',
            'D': 'Madrid'
        }
        self.assertEqual(options, expected_options)


class TestModelTest(TestCase):
    """Test Test model functionality"""
    
    def setUp(self):
        self.subject = Subject.objects.create(
            name="History",
            grade=10,
            start_time="14:00",
            questions_count=10
        )
        
        # Create questions
        self.questions = []
        for i in range(10):
            question = Question.objects.create(
                subject=self.subject,
                question_text=f"History question {i+1}",
                option_a="Option A",
                option_b="Option B",
                option_c="Option C", 
                option_d="Option D",
                correct_answer="A"
            )
            self.questions.append(question)
        
        # Create test
        self.test = Test.objects.create(subject=self.subject)
        
        # Add questions to test
        for i, question in enumerate(self.questions):
            TestQuestion.objects.create(
                test=self.test,
                question=question,
                order_number=i+1
            )
    
    def test_test_creation(self):
        """Test test creation"""
        self.assertEqual(self.test.subject, self.subject)
        self.assertTrue(self.test.is_active)
    
    def test_get_questions(self):
        """Test get_questions method"""
        test_questions = self.test.get_questions()
        self.assertEqual(test_questions.count(), 10)
    
    def test_get_participants_count(self):
        """Test get_participants_count method"""
        # Initially no participants
        self.assertEqual(self.test.get_participants_count(), 0)
        
        # Add a result
        Result.objects.create(
            test=self.test,
            student_id="12345",
            student_name="John Doe",
            score_percentage=85.0,
            total_questions=10,
            correct_answers=8
        )
        
        self.assertEqual(self.test.get_participants_count(), 1)


class ViewsTest(TestCase):
    """Test views functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        self.subject = Subject.objects.create(
            name="English",
            grade=11,
            start_time="09:00",
            questions_count=5
        )
        
        # Create questions
        for i in range(5):
            Question.objects.create(
                subject=self.subject,
                question_text=f"English question {i+1}",
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_answer="A"
            )
        
        # Create test
        self.test = Test.objects.create(subject=self.subject)
        for i, question in enumerate(Question.objects.filter(subject=self.subject)):
            TestQuestion.objects.create(
                test=self.test,
                question=question,
                order_number=i+1
            )
    
    def test_home_view(self):
        """Test home page view"""
        response = self.client.get(reverse('testapp:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bilim Sinovi')
    
    def test_test_start_view_get(self):
        """Test test start view GET request"""
        url = reverse('testapp:test_start') + f'?test_id={self.test.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.subject.name)
    
    def test_test_start_view_post(self):
        """Test test start view POST request"""
        url = reverse('testapp:test_start') + f'?test_id={self.test.id}'
        
        # Prepare form data
        form_data = {
            'student_id': '12345',
            'student_name': 'Jane Smith'
        }
        
        # Add answers for all questions
        questions = self.test.get_questions()
        for question in questions:
            form_data[f'question_{question.id}'] = 'A'
        
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 302)  # Redirect to results
        
        # Check if result was created
        result = Result.objects.filter(test=self.test, student_id='12345').first()
        self.assertIsNotNone(result)
        self.assertEqual(result.student_name, 'Jane Smith')
        self.assertEqual(result.score_percentage, 100.0)  # All answers correct
    
    def test_test_results_view(self):
        """Test test results view"""
        # Create a result first
        Result.objects.create(
            test=self.test,
            student_id="67890",
            student_name="Bob Johnson",
            score_percentage=75.0,
            total_questions=5,
            correct_answers=4
        )
        
        url = reverse('testapp:test_results') + f'?test_id={self.test.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bob Johnson')
        self.assertContains(response, '75.0%')
    
    def test_admin_login_view(self):
        """Test admin login view"""
        response = self.client.get(reverse('testapp:admin_login'))
        self.assertEqual(response.status_code, 200)
        
        # Test login
        response = self.client.post(reverse('testapp:admin_login'), {
            'username': 'admin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
    
    def test_admin_dashboard_requires_login(self):
        """Test that admin dashboard requires login"""
        response = self.client.get(reverse('testapp:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_admin_dashboard_with_login(self):
        """Test admin dashboard with authenticated user"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('testapp:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')
    
    def test_api_check_test(self):
        """Test API check test endpoint"""
        url = reverse('testapp:api_check_test') + f'?test_id={self.test.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['exists'])
        self.assertEqual(data['test']['subject'], self.subject.name)


class APITest(TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser',
            password='apipass123',
            is_staff=True
        )
        
        self.subject = Subject.objects.create(
            name="Physics",
            grade=12,
            start_time="15:00",
            questions_count=8
        )
        
        # Create questions for test creation
        for i in range(10):
            Question.objects.create(
                subject=self.subject,
                question_text=f"Physics question {i+1}",
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_answer="B"
            )
    
    def test_api_create_test(self):
        """Test API create test endpoint"""
        self.client.login(username='apiuser', password='apipass123')
        
        url = reverse('testapp:api_create_test')
        data = {'subject_id': self.subject.id}
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('test_id', response_data)
        
        # Verify test was created
        test = Test.objects.get(id=response_data['test_id'])
        self.assertEqual(test.subject, self.subject)
        self.assertEqual(test.test_questions.count(), self.subject.questions_count)
    
    def test_api_create_test_insufficient_questions(self):
        """Test API create test with insufficient questions"""
        # Create subject with more required questions than available
        subject_insufficient = Subject.objects.create(
            name="Chemistry",
            grade=9,
            start_time="16:00",
            questions_count=20  # But we only have 0 questions
        )
        
        self.client.login(username='apiuser', password='apipass123')
        
        url = reverse('testapp:api_create_test')
        data = {'subject_id': subject_insufficient.id}
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('enough', response_data['message'].lower())


class ManagementCommandTest(TestCase):
    """Test management commands"""
    
    def setUp(self):
        self.subject = Subject.objects.create(
            name="Biology",
            grade=7,
            start_time="13:00",
            questions_count=5
        )
        
        SubjectDay.objects.create(
            subject=self.subject,
            day_of_week=timezone.now().isoweekday()  # Today
        )
        
        # Create questions
        for i in range(5):
            Question.objects.create(
                subject=self.subject,
                question_text=f"Biology question {i+1}",
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_answer="C"
            )
    
    def test_create_scheduled_tests_command(self):
        """Test create_scheduled_tests management command"""
        from django.core.management import call_command
        
        # Should create test for today
        call_command('create_scheduled_tests', '--force')
        
        # Check if test was created
        test = Test.objects.filter(subject=self.subject).first()
        self.assertIsNotNone(test)
        self.assertEqual(test.test_questions.count(), 5)


class SecurityTest(TestCase):
    """Test security features"""
    
    def setUp(self):
        self.client = Client()
        
        self.subject = Subject.objects.create(
            name="Security Test Subject",
            grade=10,
            start_time="10:00",
            questions_count=3
        )
        
        # Create questions
        for i in range(3):
            Question.objects.create(
                subject=self.subject,
                question_text=f"Question {i+1}",
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
                correct_answer="A"
            )
        
        # Create test
        self.test = Test.objects.create(subject=self.subject)
        for i, question in enumerate(Question.objects.filter(subject=self.subject)):
            TestQuestion.objects.create(
                test=self.test,
                question=question,
                order_number=i+1
            )
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        from testapp.security import SecurityManager
        
        # Test valid input
        self.assertTrue(SecurityManager.validate_student_input("12345", "John Doe"))
        
        # Test SQL injection attempts
        with self.assertRaises(Exception):
            SecurityManager.validate_student_input("'; DROP TABLE users; --", "John")
        
        with self.assertRaises(Exception):
            SecurityManager.validate_student_input("12345", "John' OR '1'='1")
    
    def test_xss_protection(self):
        """Test XSS protection"""
        from testapp.security import SecurityManager
        
        # Test XSS attempts
        with self.assertRaises(Exception):
            SecurityManager.validate_student_input("12345", "<script>alert('xss')</script>")
        
        with self.assertRaises(Exception):
            SecurityManager.validate_student_input("javascript:alert(1)", "John")
    
    def test_input_length_limits(self):
        """Test input length limits"""
        from testapp.security import SecurityManager
        
        # Test long input
        long_id = "a" * 100
        long_name = "b" * 200
        
        with self.assertRaises(Exception):
            SecurityManager.validate_student_input(long_id, long_name)
    
    def test_secure_token_generation(self):
        """Test secure token generation and verification"""
        from testapp.security import SecurityManager
        
        data = "test_data"
        token = SecurityManager.generate_secure_token(data)
        
        # Should verify successfully
        self.assertTrue(SecurityManager.verify_secure_token(token, data))
        
        # Should fail with wrong data
        self.assertFalse(SecurityManager.verify_secure_token(token, "wrong_data"))
        
        # Should fail with corrupted token
        corrupted_token = token[:-5] + "xxxxx"
        self.assertFalse(SecurityManager.verify_secure_token(corrupted_token, data))


class LoadTest(TestCase):
    """Load and performance tests"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.subject = Subject.objects.create(
            name="Load Test Subject",
            grade=9,
            start_time="12:00",
            questions_count=10
        )
        
        # Create many questions
        for i in range(50):
            Question.objects.create(
                subject=self.subject,
                question_text=f"Load test question {i+1}",
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_answer="A"
            )
        
        # Create test
        self.test = Test.objects.create(subject=self.subject)
        questions = Question.objects.filter(subject=self.subject)[:10]
        for i, question in enumerate(questions):
            TestQuestion.objects.create(
                test=self.test,
                question=question,
                order_number=i+1
            )
    
    def test_concurrent_test_submissions(self):
        """Test handling concurrent test submissions"""
        import threading
        import time
        
        def submit_test(student_id):
            url = reverse('testapp:test_start') + f'?test_id={self.test.id}'
            
            form_data = {
                'student_id': f'student_{student_id}',
                'student_name': f'Student {student_id}'
            }
            
            # Add answers
            questions = self.test.get_questions()
            for question in questions:
                form_data[f'question_{question.id}'] = 'A'
            
            response = self.client.post(url, form_data)
            return response.status_code
        
        # Create multiple threads
        threads = []
        results = []
        
        for i in range(10):
            thread = threading.Thread(
                target=lambda i=i: results.append(submit_test(i))
            )
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All submissions should succeed
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIn(result, [200, 302])  # Success or redirect
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 10)  # Less than 10 seconds
        
        # Verify all results were created
        self.assertEqual(Result.objects.filter(test=self.test).count(), 10)
    
    def test_large_results_view_performance(self):
        """Test performance with large number of results"""
        import time
        
        # Create many results
        for i in range(100):
            Result.objects.create(
                test=self.test,
                student_id=f'perf_test_{i}',
                student_name=f'Performance Test Student {i}',
                score_percentage=80.0 + (i % 20),  # Vary scores
                total_questions=10,
                correct_answers=8 + (i % 3)
            )
        
        # Test results view performance
        url = reverse('testapp:test_results') + f'?test_id={self.test.id}'
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2)  # Should load in under 2 seconds