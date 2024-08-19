from nomad.datamodel.datamodel import EntryArchive
from nomad.datamodel.summary import mapping_base_classes
from nomad.normalizing import Normalizer
from structlog.stdlib import BoundLogger


def recurse_instance(root):
    """Generator that recursively returns section instances found in the given
    root section.
    """
    if not root:
        return
    for key in root.__dict__:
        section_def = root.m_def.all_sub_sections.get(key)
        if section_def is None:
            continue

        for sub_section in root.m_get_sub_sections(section_def):
            yield sub_section
            yield from recurse_instance(sub_section)


def remove_non_scalar(d):
    """
    Recursively removes all non-scalar values from a dictionary.

    :param d: The dictionary to process.
    :return: The processed dictionary with only scalar values.
    """
    if not isinstance(d, dict):
        raise ValueError('Input must be a dictionary')

    keys_to_delete = []

    for key, value in d.items():
        # Clean up dictionaries recursively
        if isinstance(value, dict):
            remove_non_scalar(value)
            if not value:
                keys_to_delete.append(key)
        # Clean up lists recursively
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                d[key] = [remove_non_scalar(v) for v in value]
            else:
                keys_to_delete.append(key)
    for key in keys_to_delete:
        del d[key]

    return d


class SummaryNormalizer(Normalizer):
    """This normalizer will crawl over the `archive.data` section and fill the
    `archive.summary` according to the usage of NOMAD base sections (see
    https://nomad-lab.eu/prod/v1/docs/howto/customization/base_sections.html).
    """

    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:
        super().normalize(archive, logger)

        # Loop over base classes and store into summary
        for section in recurse_instance(archive.data):
            summary_info = mapping_base_classes.get(type(section))
            if summary_info:
                try:
                    # Remove non-scalar values
                    values = remove_non_scalar(section.m_to_dict())

                    # Create a separate dictionary containing the n_* arguments
                    # that are needed in the class initialization.
                    n_args = {}
                    for key, value in values.items():
                        if key.startswith('n_'):
                            n_args[key] = value
                    summary_data = summary_info[0](**n_args)

                    # Update with the rest of the data
                    summary_data.m_update_from_dict(values)

                    # Store reference to the original data
                    summary_data.reference = section

                    base = archive.m_setdefault(summary_info[1])
                    base.m_add_sub_section(
                        getattr(type(base), summary_info[2]), summary_data
                    )
                except Exception as e:
                    self.logger.error('exception during packing archives', exc_info=e)
