SELECT
    ProcedureDefinition,
    ProcedureDefinition.ExternalID,
    _ProcedureInstance_key,
    OutputValue,
    DateDue,
    OrganismID,
    DateBirth,
    StockNumber
FROM
    Organism
        INNER JOIN
    ProcedureInstanceOrganism USING (_Organism_key)
        INNER JOIN
    ProcedureInstance USING (_ProcedureInstance_key)
        INNER JOIN
    OutputInstanceSet USING (_ProcedureInstance_key)
        INNER JOIN
    Outputinstance USING (_outputInstanceSet_key)
        INNER JOIN
    Output USING (_Output_key)
        INNER JOIN
    ProcedureDefinitionVersion USING (_ProcedureDefinitionVersion_key)
        INNER JOIN
    ProcedureDefinition USING (_ProcedureDefinition_key)
        INNER JOIN
    Line USING (_Line_key)
WHERE
    Output._DataType_key = 7
        AND OutputValue NOT LIKE '%omeroweb%'
        AND CHAR_LENGTH(OutputValue) > 0
        AND Output.ExternalID IS NOT NULL;