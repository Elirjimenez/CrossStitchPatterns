from app.domain.model.project import PatternResult
from app.infrastructure.persistence.models.pattern_result_model import PatternResultModel


class PatternResultMapper:
    @staticmethod
    def to_model(domain: PatternResult) -> PatternResultModel:
        return PatternResultModel(
            id=domain.id,
            project_id=domain.project_id,
            created_at=domain.created_at,
            palette=domain.palette,
            grid_width=domain.grid_width,
            grid_height=domain.grid_height,
            stitch_count=domain.stitch_count,
            pdf_ref=domain.pdf_ref,
            processing_mode=domain.processing_mode,
            variant=domain.variant,
            aida_count=domain.aida_count,
            margin_cm=domain.margin_cm,
        )

    @staticmethod
    def to_domain(model: PatternResultModel) -> PatternResult:
        return PatternResult(
            id=model.id,
            project_id=model.project_id,
            created_at=model.created_at,
            palette=model.palette,
            grid_width=model.grid_width,
            grid_height=model.grid_height,
            stitch_count=model.stitch_count,
            pdf_ref=model.pdf_ref,
            processing_mode=model.processing_mode or "auto",
            variant=model.variant or "color",
            aida_count=model.aida_count if model.aida_count is not None else 14,
            margin_cm=model.margin_cm if model.margin_cm is not None else 5.0,
        )
