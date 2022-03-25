import typing

FilterType = typing.Literal["activity", "date", "character"]
OperatorType = typing.Literal["after", "before", "is", "is not", "in", "not in"]


class ActivityFilterList:
    def __init__(self):
        pass

    filters: list = []

    def addFilter(self, filterType: FilterType, operator: OperatorType, value) -> None:
        """
        Adds a filter to filter activities by.

        Possible filters are:

        - "activity", filters by activity type. CURRENTLY BROKEN AND WILL NOT CHANGE BATCHES.
          - supported operators: "is", "is not", "in", "not in"
          - value type: A GameMode value (or a list, depending on the operator)
                        See aiobungie.GameMode for a mapping.

        - "date", filters by activity date
          - supported operators: "before", "after"
          - value type: A string in the ISO format.
                        Important: Needs to have a time and timezone, cannot use "Z" timezone.

        - "character", filters by class
          - supported operators: "is", "is not", "in", "not in"
          - value type: A Class value (or a list, depending on the operator)
                        See aiobungie.Class for a mapping.

        :param filterType: A valid filter type.
        :param operator: A valid operator.
        :param value: The value to filter by.
        """
        self.filters.append({
            "type": filterType,
            "operator": operator,
            "value": value
        })

    def getFilters(self) -> list:
        return self.filters
