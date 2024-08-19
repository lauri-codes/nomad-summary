from nomad.config.models.plugins import NormalizerEntryPoint


class SummaryNormalizerEntryPoint(NormalizerEntryPoint):
    def load(self):
        from nomad_summary.normalizers.summarynormalizer import SummaryNormalizer

        return SummaryNormalizer(**self.dict())


summarynormalizer = SummaryNormalizerEntryPoint(
    name='SummaryNormalizer',
    description="""
    Normalizer that fills archive.summary based on the NOMAD base sections that
    are present in archive.data
    """,
)
