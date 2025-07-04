# testapp/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Subject, SubjectDay, Question
import json

class LoginForm(forms.Form):
    """Admin login formasi"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )


class SubjectForm(forms.ModelForm):
    """Fan qo'shish/tahrirlash formasi"""
    
    # Hafta kunlari uchun checkbox field
    days = forms.MultipleChoiceField(
        choices=SubjectDay.DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Hafta kunlari"
    )
    
    class Meta:
        model = Subject
        fields = ['name', 'grade', 'start_time', 'questions_count']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject name',
            }),
            'grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 11,
                'placeholder': 'Grade (1-11)',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'questions_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 50,
                'placeholder': 'Questions count (5-50)',
            }),
        }
        labels = {
            'name': 'Fan nomi',
            'grade': 'Sinf',
            'start_time': 'Boshlanish vaqti',
            'questions_count': 'Test savollar soni',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agar mavjud fanni tahrirlamoqchi bo'lsak, uning kunlarini olish
        if self.instance and self.instance.pk:
            self.fields['days'].initial = [
                str(day.day_of_week) for day in self.instance.subject_days.all()
            ]
    
    def clean_questions_count(self):
        questions_count = self.cleaned_data.get('questions_count')
        if questions_count < 5 or questions_count > 50:
            raise ValidationError('Savollar soni 5 dan 50 gacha bo\'lishi kerak!')
        return questions_count
    
    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade < 1 or grade > 11:
            raise ValidationError('Sinf 1 dan 11 gacha bo\'lishi kerak!')
        return grade
    
    def save(self, commit=True):
        subject = super().save(commit=commit)
        
        if commit:
            # Avval eski kunlarni o'chirish
            subject.subject_days.all().delete()
            
            # Yangi kunlarni qo'shish
            days = self.cleaned_data.get('days', [])
            for day in days:
                SubjectDay.objects.create(
                    subject=subject,
                    day_of_week=int(day)
                )
        
        return subject


class QuestionForm(forms.ModelForm):
    """Savol qo'shish/tahrirlash formasi"""
    
    class Meta:
        model = Question
        fields = ['subject', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Savol matnini kiriting'
            }),
            'option_a': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A variant'
            }),
            'option_b': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'B variant'
            }),
            'option_c': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'C variant'
            }),
            'option_d': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'D variant'
            }),
            'correct_answer': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'subject': 'Fan',
            'question_text': 'Savol matni',
            'option_a': 'A variant',
            'option_b': 'B variant',
            'option_c': 'C variant',
            'option_d': 'D variant',
            'correct_answer': 'To\'g\'ri javob',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Barcha variantlar to'ldirilganligini tekshirish
        options = [
            cleaned_data.get('option_a'),
            cleaned_data.get('option_b'),
            cleaned_data.get('option_c'),
            cleaned_data.get('option_d'),
        ]
        
        if not all(options):
            raise ValidationError('Barcha variantlar to\'ldirilishi shart!')
        
        # Variantlar takrorlanmasligini tekshirish
        if len(set(options)) != len(options):
            raise ValidationError('Variantlar takrorlanmasligi kerak!')
        
        return cleaned_data


class BulkQuestionForm(forms.Form):
    """Ko'plab savollar qo'shish formasi"""
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Fan",
        empty_label="Select a subject",
    )
    
    # JavaScript orqali to'ldiriladi
    questions_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def clean_questions_json(self):
        questions_json = self.cleaned_data.get('questions_json')
        
        if not questions_json:
            raise ValidationError('Hech bo\'lmaganda bitta savol qo\'shing!')
        
        try:
            questions_data = json.loads(questions_json)
        except json.JSONDecodeError:
            raise ValidationError('Savollar ma\'lumotlarida xatolik!')
        
        if len(questions_data) == 0:
            raise ValidationError('Hech bo\'lmaganda bitta savol qo\'shing!')
        
        if len(questions_data) > 50:
            raise ValidationError('Bir vaqtda 50 tadan ko\'p savol qo\'shib bo\'lmaydi!')
        
        # Har bir savolni validatsiya qilish
        for i, q_data in enumerate(questions_data, 1):
            required_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            
            for field in required_fields:
                if not q_data.get(field):
                    raise ValidationError(f'{i}-savol uchun {field} maydonini to\'ldiring!')
            
            # To'g'ri javob tekshirish
            if q_data.get('correct_answer') not in ['A', 'B', 'C', 'D']:
                raise ValidationError(f'{i}-savol uchun to\'g\'ri javob A, B, C yoki D bo\'lishi kerak!')
            
            # Variantlar takrorlanmasligini tekshirish
            options = [q_data.get('option_a'), q_data.get('option_b'), q_data.get('option_c'), q_data.get('option_d')]
            if len(set(options)) != len(options):
                raise ValidationError(f'{i}-savol uchun variantlar takrorlanmasligi kerak!')
        
        return questions_data
    
    def clean(self):
        cleaned_data = super().clean()
        
        # questions_json ni questions_data ga o'tkazish
        questions_data = cleaned_data.get('questions_json')
        if questions_data:
            cleaned_data['questions_data'] = questions_data
        
        return cleaned_data