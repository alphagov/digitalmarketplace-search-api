import hashlib
import six

import app.mapping
from .conversions import strip_and_lowercase


def process_values_for_matching(values):
    if isinstance(values, list):
        return [strip_and_lowercase(value) for value in values]
    elif isinstance(values, six.string_types):
        return strip_and_lowercase(values)

    return values


def _ensure_value_list(json_string_or_list):
    if isinstance(json_string_or_list, list):
        return json_string_or_list
    else:
        return [json_string_or_list]


def _append_conditionally(arguments, document):
    """
    A transformation processor that generates new field values in "target field" when
    certain values are present in "field". The example use case is when
    we are adding parent categories, whenever any one of their subcategories
    is present.
    :param arguments: dict -- the parameters to the processor as specified in configuration
    :param document: dict -- the Elasticsearch document that we are transforming
    """
    source_field = arguments['field']
    target_field = arguments.get('target_field') or source_field

    if source_field in document:
        source_values = _ensure_value_list(document[source_field])
        source_values_set = set(source_values)
        target_values = _ensure_value_list(document.get(target_field, []))

        if any(value in source_values_set for value in arguments['any_of']):
            target_values.extend(arguments['append_value'])
            # "append_value" key singular despite being a list, consistent with Elasticsearch practice
            document[target_field] = target_values


def _copyhash_to(arguments, document):
    """
    A transformation processor that performs a sha256 on the (utf8) string representation of the "field" and stores
    the (lowercase hex string) result on the document under a key specified by "target_field". If "target_field" is not
    specified, the source field will be overwritten with the result.
    :param arguments: dict -- the parameters to the processor as specified in configuration
    :param document: dict -- the Elasticsearch document that we are transforming
    """
    source_field = arguments['field']
    target_field = arguments.get('target_field') or source_field

    if source_field in document:
        document[target_field] = hashlib.sha256((six.text_type(document[source_field])).encode('utf-8')).hexdigest()


TRANSFORMATION_PROCESSORS = {
    'append_conditionally': _append_conditionally,
    'copyhash_to': _copyhash_to,
}


def convert_request_json_into_index_json(mapping, request_json):
    index_json = {}
    for transformation in mapping.transform_fields:
        # Each transformation is a dictionary, with a type mapping to the arguments pertaining to
        # that type. We anticipate only one type per transformation (consistent with how 'ingest
        # processors' are specified for Elasticsearch - see
        # <https://www.elastic.co/guide/en/elasticsearch/reference/current/ingest-processors.html>).

        for transformation_type, transformation_arguments in transformation.items():
            TRANSFORMATION_PROCESSORS[transformation_type](transformation_arguments, request_json)

    for field in request_json:
        if field in mapping.filter_fields_set:
            index_json["filter_" + field] = process_values_for_matching(
                request_json[field]
            )
        if field in mapping.non_filter_fields_set:
            index_json[field] = request_json[field]

    return index_json
