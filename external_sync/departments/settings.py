csv_quotechar = '"'
csv_delimiter = ';'

# CSV column name containing the internal name (must always be set)
internal_name = "CRM-Gebietsname"

# CSV column names for the hierarchical structure (multiple names mean two columns have the same depth)
name_fields = ["Name (Bundeslevel)", "Name (Landeslevel)", "Name (BV-Level)",
               ["Name (Kreis-Fusion)", "Name (Kreis-Level)"], "Name (Orts-Level)"]
# Index into the name_fields array for the default name which gets all departments with invalid naming
name_default = 1

# Departments with this disbanded date being earlier than today are ignored
ignore_after_name = "Auflösung"
ignore_after_format = "%d.%m.%Y"
