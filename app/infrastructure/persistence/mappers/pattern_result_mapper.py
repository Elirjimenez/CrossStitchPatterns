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
        )
