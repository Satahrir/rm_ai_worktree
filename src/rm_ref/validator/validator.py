from rm_ref.config import ResolvedConfig
from rm_ref.schema import SchemaDefinition
from rm_ref.validator.errors import ValidationSetupError
from rm_ref.validator.result import ValidationIssue, ValidationResult
from rm_ref.validator.rules import validate_mapping


class Validator(object):
    def __init__(self, schema, rules=None):
        if not isinstance(schema, SchemaDefinition):
            raise ValidationSetupError("schema must be SchemaDefinition")
        self.schema = schema
        self.rules = []
        for rule in rules or []:
            self.add_rule(rule)

    def add_rule(self, rule):
        if not callable(rule):
            raise ValidationSetupError("validation rule must be callable")
        self.rules.append(rule)
        return self

    def _collect_rule_output(self, output, result):
        if output is None:
            return
        if isinstance(output, ValidationIssue):
            result.add(output)
            return
        if isinstance(output, (list, tuple)):
            for issue in output:
                result.add(issue)
            return
        raise ValidationSetupError(
            "custom validation rule returned unsupported value {0!r}".format(
                output
            )
        )

    def validate(self, resolved_config):
        if not isinstance(resolved_config, ResolvedConfig):
            raise ValidationSetupError(
                "resolved_config must be ResolvedConfig"
            )
        if resolved_config.schema_id != self.schema.schema_id:
            raise ValidationSetupError(
                "resolved config schema_id {0!r} does not match schema {1!r}".format(
                    resolved_config.schema_id, self.schema.schema_id
                )
            )

        result = ValidationResult()
        validate_mapping(
            resolved_config.global_values,
            self.schema.fields_for_scope("global"),
            self.schema.schema_id,
            result,
        )
        for packet in resolved_config.packets:
            validate_mapping(
                packet.values,
                self.schema.fields_for_scope("packet"),
                self.schema.schema_id,
                result,
                packet_index=packet.packet_index,
            )
            for cell in packet.cells:
                validate_mapping(
                    cell.values,
                    self.schema.fields_for_scope("cell"),
                    self.schema.schema_id,
                    result,
                    packet_index=packet.packet_index,
                    cell_index=cell.cell_index,
                )

        for rule in self.rules:
            output = rule(resolved_config, self.schema, result)
            self._collect_rule_output(output, result)
        return result
