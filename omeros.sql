SELECT
    ProcedureDefinition, ProcedureDefinition.ExternalID, OutputName, OutputValue, _procedureInstance_Key as TestCode
FROM
    proceduredefinition
        INNER JOIN
    proceduredefinitionversion USING (_ProcedureDefinition_key)
        INNER JOIN
    ProcedureInstance USING (_ProcedureDefinitionVersion_key)
        INNER JOIN
        outputInstanceSet USING (_ProcedureInstance_key)
        inner join
    outputinstance USING (_outputInstanceSet_key)
        INNER JOIN
    Output USING (_Output_key)
WHERE
CHAR_LENGTH(OutputValue) > 0 AND
OutputValue LIKE '%omeroweb%' AND
    outputinstance._Output_key IN (1842 , 2148, 4628);