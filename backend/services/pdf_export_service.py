"""
PDF Export Service - Generate beautiful PDFs for meal plans, schedules, and wellness reports

Uses ReportLab for complex layouts and Jinja2 + WeasyPrint for HTML-to-PDF conversion
"""
from typing import Optional, List, Dict
from datetime import date, datetime
from io import BytesIO
import os
from pathlib import Path

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, Frame, FrameBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Jinja2 for templating
from jinja2 import Environment, FileSystemLoader, Template

from backend.models.life_optimization_models import (
    DailyMealPlan,
    WeeklyMealPlan,
    DailySchedule,
    ComprehensiveUserProfile
)
from backend.services.shopping_list_service import ShoppingList


class PDFExportService:
    """Generate beautiful PDFs for wellness data"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))

        # Small text for notes
        self.styles.add(ParagraphStyle(
            name='SmallNotes',
            parent=self.styles['BodyText'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            leading=10
        ))

    def generate_meal_plan_pdf(
        self,
        meal_plan: DailyMealPlan,
        profile: Optional[ComprehensiveUserProfile] = None
    ) -> BytesIO:
        """
        Generate PDF for a single day's meal plan

        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title
        title = Paragraph(
            f"Daily Meal Plan - {meal_plan.date}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Summary stats
        summary_data = [
            ['Total Calories', f"{int(meal_plan.total_calories)}"],
            ['Protein', f"{int(meal_plan.total_protein)}g"],
            ['Carbs', f"{int(meal_plan.total_carbs)}g"],
            ['Fat', f"{int(meal_plan.total_fat)}g"],
            ['Total Cost', f"${meal_plan.total_cost:.2f}"],
            ['Dosha Balance', f"{int(meal_plan.dosha_balance_score)}/100"]
        ]

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f2f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Compliance indicators
        compliance = []
        if meal_plan.meets_goals:
            compliance.append("✓ Meets Nutritional Goals")
        if meal_plan.meets_budget:
            compliance.append("✓ Within Budget")

        if compliance:
            compliance_text = Paragraph(
                " | ".join(compliance),
                self.styles['CustomBody']
            )
            story.append(compliance_text)
            story.append(Spacer(1, 0.2 * inch))

        # Meals
        for meal in meal_plan.meals:
            # Meal header
            meal_header = Paragraph(
                f"<b>{meal.time} - {meal.meal_type.upper()}: {meal.name}</b>",
                self.styles['CustomSubtitle']
            )
            story.append(meal_header)

            # Description
            if meal.description:
                desc = Paragraph(meal.description, self.styles['CustomBody'])
                story.append(desc)

            # Ingredients
            story.append(Paragraph("<b>Ingredients:</b>", self.styles['SectionHeader']))

            ingredients_data = [['Ingredient', 'Quantity', 'Reason']]
            for ing in meal.ingredients:
                ingredients_data.append([
                    ing.name,
                    f"{ing.quantity} {ing.unit}",
                    ing.reason or ""
                ])

            ingredients_table = Table(
                ingredients_data,
                colWidths=[1.8 * inch, 1.2 * inch, 3 * inch]
            )
            ingredients_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(ingredients_table)
            story.append(Spacer(1, 0.1 * inch))

            # Cooking instructions
            if meal.cooking_instructions:
                story.append(Paragraph("<b>Instructions:</b>", self.styles['SectionHeader']))
                for idx, instruction in enumerate(meal.cooking_instructions, 1):
                    inst_text = Paragraph(
                        f"{idx}. {instruction}",
                        self.styles['CustomBody']
                    )
                    story.append(inst_text)
                story.append(Spacer(1, 0.1 * inch))

            # Nutrition
            nutrition_data = [
                ['Calories', 'Protein', 'Carbs', 'Fat', 'Cost'],
                [
                    f"{int(meal.total_nutrients.calories)}",
                    f"{int(meal.total_nutrients.protein_g)}g",
                    f"{int(meal.total_nutrients.carbs_g)}g",
                    f"{int(meal.total_nutrients.fat_g)}g",
                    f"${meal.cost_total:.2f}"
                ]
            ]

            nutrition_table = Table(nutrition_data, colWidths=[1.2 * inch] * 5)
            nutrition_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e1f5ff')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(nutrition_table)

            # Timing reason
            if meal.timing_reason:
                timing = Paragraph(
                    f"<i>Why this timing? {meal.timing_reason}</i>",
                    self.styles['SmallNotes']
                )
                story.append(timing)

            story.append(Spacer(1, 0.3 * inch))

        # Footer
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Wellness AI - Your Personal Holistic Health Companion",
            self.styles['SmallNotes']
        )
        story.append(footer)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_weekly_meal_plan_pdf(
        self,
        weekly_plan: WeeklyMealPlan,
        profile: Optional[ComprehensiveUserProfile] = None
    ) -> BytesIO:
        """Generate PDF for weekly meal plan"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title
        title = Paragraph(
            f"Weekly Meal Plan - {weekly_plan.start_date} to {weekly_plan.end_date}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Weekly summary
        summary = Paragraph(
            f"<b>Total Week Cost:</b> ${weekly_plan.total_week_cost:.2f} | "
            f"<b>Avg Daily Calories:</b> {int(weekly_plan.average_daily_calories)} | "
            f"<b>Dosha Balance:</b> {int(weekly_plan.average_dosha_balance)}/100",
            self.styles['CustomBody']
        )
        story.append(summary)
        story.append(Spacer(1, 0.3 * inch))

        # Daily plans
        for daily_plan in weekly_plan.daily_plans:
            # Each day on a new page
            if daily_plan != weekly_plan.daily_plans[0]:
                story.append(PageBreak())

            # Day header
            day_header = Paragraph(
                f"<b>{daily_plan.date.strftime('%A, %B %d, %Y')}</b>",
                self.styles['CustomSubtitle']
            )
            story.append(day_header)

            # Day meals (abbreviated)
            for meal in daily_plan.meals:
                meal_summary = Paragraph(
                    f"• <b>{meal.time} - {meal.meal_type.upper()}:</b> {meal.name} "
                    f"({int(meal.total_nutrients.calories)} cal, ${meal.cost_total:.2f})",
                    self.styles['CustomBody']
                )
                story.append(meal_summary)

            story.append(Spacer(1, 0.2 * inch))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_shopping_list_pdf(self, shopping_list: ShoppingList) -> BytesIO:
        """Generate PDF for shopping list"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title
        title = Paragraph(
            f"Shopping List - {shopping_list.start_date} to {shopping_list.end_date}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Summary
        summary = Paragraph(
            f"<b>{shopping_list.total_items} items</b> for <b>{shopping_list.num_days} days</b> | "
            f"<b>Total Cost:</b> {shopping_list.formatted_total_cost}",
            self.styles['CustomBody']
        )
        story.append(summary)
        story.append(Spacer(1, 0.3 * inch))

        # Items by category
        for category, items in shopping_list.items_by_category.items():
            # Category header
            category_header = Paragraph(
                f"<b>{category.upper()}</b>",
                self.styles['SectionHeader']
            )
            story.append(category_header)

            # Items table
            items_data = [['□', 'Item', 'Quantity', 'Cost', 'Notes']]

            for item in items:
                items_data.append([
                    '',  # Checkbox
                    item.name,
                    f"{item.total_quantity} {item.unit}",
                    item.formatted_cost,
                    item.notes or ''
                ])

            items_table = Table(
                items_data,
                colWidths=[0.3 * inch, 1.8 * inch, 1 * inch, 0.9 * inch, 2 * inch]
            )
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ca02c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            story.append(items_table)
            story.append(Spacer(1, 0.2 * inch))

        # Footer
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Wellness AI",
            self.styles['SmallNotes']
        )
        story.append(footer)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_schedule_pdf(self, schedule: DailySchedule) -> BytesIO:
        """Generate PDF for daily schedule"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title
        title = Paragraph(
            f"Daily Schedule - {schedule.date}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Summary
        summary_data = [
            ['Sleep', f"{schedule.sleep_hours}h"],
            ['Work', f"{schedule.work_hours}h"],
            ['Exercise', f"{schedule.exercise_minutes} min"],
            ['Meditation', f"{schedule.meditation_minutes} min"],
            ['Free Time', f"{schedule.free_time_minutes} min"]
        ]

        summary_table = Table(summary_data, colWidths=[1.5 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f2f6')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Energy forecast
        if schedule.energy_forecast:
            forecast_text = Paragraph(
                f"<b>Energy Forecast:</b> Morning: {schedule.energy_forecast.get('morning', 'N/A').title()} | "
                f"Afternoon: {schedule.energy_forecast.get('afternoon', 'N/A').title()} | "
                f"Evening: {schedule.energy_forecast.get('evening', 'N/A').title()}",
                self.styles['CustomBody']
            )
            story.append(forecast_text)
            story.append(Spacer(1, 0.2 * inch))

        # Activities timeline
        story.append(Paragraph("<b>Daily Timeline</b>", self.styles['SectionHeader']))

        activities_data = [['Time', 'Activity', 'Duration', 'Reason']]

        for activity in schedule.activities:
            activities_data.append([
                activity.time,
                activity.title,
                f"{activity.duration_minutes} min",
                activity.reason or ''
            ])

        activities_table = Table(
            activities_data,
            colWidths=[0.8 * inch, 2 * inch, 0.8 * inch, 2.5 * inch]
        )
        activities_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(activities_table)

        # Footer
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Wellness AI",
            self.styles['SmallNotes']
        )
        story.append(Spacer(1, 0.3 * inch))
        story.append(footer)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_wellness_report_pdf(
        self,
        user_id: str,
        profile: ComprehensiveUserProfile,
        wellness_scores: Dict,
        recent_data: Dict
    ) -> BytesIO:
        """Generate comprehensive wellness report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Cover page
        title = Paragraph(
            "Holistic Wellness Report",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))

        # User info
        user_info = Paragraph(
            f"<b>User ID:</b> {user_id}<br/>"
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
            f"<b>Dosha Type:</b> {profile.personality.dosha_type}<br/>"
            f"<b>Primary Goal:</b> {profile.goals.primary_goal.value.replace('_', ' ').title()}",
            self.styles['CustomBody']
        )
        story.append(user_info)
        story.append(Spacer(1, 0.5 * inch))

        # Wellness scores
        story.append(Paragraph("<b>Wellness Scores (0-100)</b>", self.styles['SectionHeader']))

        scores_data = [['Dimension', 'Score', 'Status']]
        for dimension, score in wellness_scores.items():
            status = "Excellent" if score >= 80 else "Good" if score >= 60 else "Needs Attention"
            scores_data.append([dimension.title(), f"{int(score)}", status])

        scores_table = Table(scores_data, colWidths=[2 * inch, 1 * inch, 1.5 * inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(scores_table)
        story.append(Spacer(1, 0.3 * inch))

        # Recent data summary
        if recent_data:
            story.append(Paragraph("<b>Recent Activity Summary</b>", self.styles['SectionHeader']))

            for key, value in recent_data.items():
                item = Paragraph(f"• <b>{key}:</b> {value}", self.styles['CustomBody'])
                story.append(item)

            story.append(Spacer(1, 0.3 * inch))

        # Recommendations
        story.append(Paragraph("<b>Personalized Recommendations</b>", self.styles['SectionHeader']))

        recommendations = [
            "Continue your daily meditation practice for stress management",
            "Consider adding magnesium-rich foods to support sleep quality",
            "Maintain current exercise routine - consistency is excellent",
            "Schedule regular breaks during work hours to prevent burnout"
        ]

        for rec in recommendations:
            rec_para = Paragraph(f"• {rec}", self.styles['CustomBody'])
            story.append(rec_para)

        story.append(Spacer(1, 0.5 * inch))

        # Footer
        footer = Paragraph(
            "This report is for informational purposes only and does not constitute medical advice. "
            "Always consult qualified healthcare professionals for medical guidance.",
            self.styles['SmallNotes']
        )
        story.append(footer)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer


# Singleton instance
_pdf_service = None


def get_pdf_service() -> PDFExportService:
    """Get singleton instance of PDF export service"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFExportService()
    return _pdf_service
