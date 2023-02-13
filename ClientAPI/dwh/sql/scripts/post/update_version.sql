DELETE FROM changelog
WHERE "version" = {DWH_VERSION};

INSERT INTO changelog ("version", updated)
VALUES ({DWH_VERSION}, GETDATE());
