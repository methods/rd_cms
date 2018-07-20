import csv
from io import StringIO

chart = {
    "type": "bar",
    "title": {
        "text": "Percentage of adults who had fear crime by ethnicity"
    },
    "xAxis": {
        "title": {
            "text": "%"
        },
        "categories": [
            "Asian",
            "Black",
            "Mixed",
            "Other",
            "White"
        ]
    },
    "yAxis": {
        "title": {}
    },
    "series": [
        {
            "name": "2013/14",
            "data": [
                31.5,
                26.8,
                28.6,
                25.1,
                17.9
            ],
            "name_value": 2013
        },
        {
            "name": "2014/15",
            "data": [
                28.2,
                23.7,
                20.3,
                26,
                17.4
            ],
            "name_value": 2014
        },
        {
            "name": "2015/16",
            "data": [
                27.1,
                26.3,
                21.1,
                27.1,
                18
            ],
            "name_value": 2015
        }
    ],
    "number_format": {
        "multiplier": 1,
        "prefix": "",
        "suffix": "%",
        "min": 0,
        "max": 100
    }
}

chart_source_data = {
    "data": [
        [
            "Measure",
            "Time",
            "Ethnicity",
            "Value"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "White",
            "17.9"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Mixed",
            "28.6"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Asian",
            "31.5"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Black",
            "26.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Other",
            "25.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "White",
            "17.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Mixed",
            "20.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Asian",
            "28.2"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Black",
            "23.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Other",
            "26.0"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "White",
            "18.0"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Mixed",
            "21.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Asian",
            "27.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Black",
            "26.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Other",
            "27.1"
        ]
    ],
    "type": "bar_chart",
    "chartOptions": {
        "primary_column": "Ethnicity",
        "secondary_column": "Time",
        "x_axis_column": "Time",
        "line_series_column": "Ethnicity",
        "component_bar_column": "Ethnicity",
        "component_component_column": "[None]"
    },
    "chartFormat": {
        "chart_title": "Percentage of adults who had fear crime by ethnicity",
        "x_axis_label": "%",
        "y_axis_label": "",
        "number_format": "percent",
        "number_format_prefix": "",
        "number_format_suffix": "",
        "number_format_min": "",
        "number_format_max": ""
    }
}


def data_to_csv(source_data):
    csv_columns = source_data['data'][0]
    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(csv_columns)
        for row in source_data['data'][1:]:
            writer.writerow(row)
        contents = output.getvalue()
    return contents


table = {
    "group_columns": [
        "",
        "2013/14",
        "2014/15",
        "2015/16"
    ],
    "type": "grouped",
    "header": "Table from mock data",
    "category": "Ethnicity",
    "columns": [
        "%"
    ],
    "data": [
        {
            "category": "White",
            "values": [
                "17.9",
                "17.4",
                "18.0"
            ]
        },
        {
            "category": "White British",
            "values": [
                "17.7",
                "17.4",
                "17.8"
            ]
        },
        {
            "category": "White Irish",
            "values": [
                "20.7",
                "17.5",
                "20.4"
            ]
        },
        {
            "category": "Gypsy or Irish Traveller",
            "values": [
                "-",
                "-",
                "-"
            ]
        },
        {
            "category": "Any other white background",
            "values": [
                "20.4",
                "18.7",
                "20.7"
            ]
        },
        {
            "category": "Mixed",
            "values": [
                "28.6",
                "20.3",
                "21.1"
            ]
        },
        {
            "category": "Mixed white and black caribbean",
            "values": [
                "24.9",
                "21.4",
                "17.7"
            ]
        },
        {
            "category": "Mixed white and black african",
            "values": [
                "-",
                "-",
                "-"
            ]
        },
        {
            "category": "Mixed white and asian",
            "values": [
                "32.7",
                "17.8",
                "21.4"
            ]
        },
        {
            "category": "Any other Mixed/Multiple ethnic background",
            "values": [
                "24.8",
                "26.8",
                "26.3"
            ]
        },
        {
            "category": "Asian",
            "values": [
                "31.5",
                "28.2",
                "27.1"
            ]
        },
        {
            "category": "Indian",
            "values": [
                "33.3",
                "29.3",
                "27.5"
            ]
        },
        {
            "category": "Pakistani",
            "values": [
                "35.3",
                "27.5",
                "29.8"
            ]
        },
        {
            "category": "Bangladeshi",
            "values": [
                "34.2",
                "29.1",
                "31.4"
            ]
        },
        {
            "category": "Chinese",
            "values": [
                "15.3",
                "19.3",
                "15.7"
            ]
        },
        {
            "category": "Any other asian",
            "values": [
                "28.8",
                "30.3",
                "25.7"
            ]
        },
        {
            "category": "Black",
            "values": [
                "26.8",
                "23.7",
                "26.3"
            ]
        },
        {
            "category": "Black african",
            "values": [
                "23.2",
                "22.2",
                "25.4"
            ]
        },
        {
            "category": "Black caribbean",
            "values": [
                "31.9",
                "25.7",
                "27.7"
            ]
        },
        {
            "category": "Any other black background",
            "values": [
                "-",
                "26.2",
                "28.1"
            ]
        },
        {
            "category": "Other",
            "values": [
                "25.1",
                "26.0",
                "27.1"
            ]
        },
        {
            "category": "Arab",
            "values": [
                "21.4",
                "25.5",
                "29.7"
            ]
        },
        {
            "category": "Any other ethnic group",
            "values": [
                "27.3",
                "26.3",
                "25.5"
            ]
        }
    ],
    "title": {
        "text": "Grouped Table"
    },
    "groups": [
        {
            "group": "2013/14",
            "data": [
                {
                    "category": "White",
                    "values": [
                        "17.9"
                    ]
                },
                {
                    "category": "White British",
                    "values": [
                        "17.7"
                    ]
                },
                {
                    "category": "White Irish",
                    "values": [
                        "20.7"
                    ]
                },
                {
                    "category": "Gypsy or Irish Traveller",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Any other white background",
                    "values": [
                        "20.4"
                    ]
                },
                {
                    "category": "Mixed",
                    "values": [
                        "28.6"
                    ]
                },
                {
                    "category": "Mixed white and black caribbean",
                    "values": [
                        "24.9"
                    ]
                },
                {
                    "category": "Mixed white and black african",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Mixed white and asian",
                    "values": [
                        "32.7"
                    ]
                },
                {
                    "category": "Any other Mixed/Multiple ethnic background",
                    "values": [
                        "24.8"
                    ]
                },
                {
                    "category": "Asian",
                    "values": [
                        "31.5"
                    ]
                },
                {
                    "category": "Indian",
                    "values": [
                        "33.3"
                    ]
                },
                {
                    "category": "Pakistani",
                    "values": [
                        "35.3"
                    ]
                },
                {
                    "category": "Bangladeshi",
                    "values": [
                        "34.2"
                    ]
                },
                {
                    "category": "Chinese",
                    "values": [
                        "15.3"
                    ]
                },
                {
                    "category": "Any other asian",
                    "values": [
                        "28.8"
                    ]
                },
                {
                    "category": "Black",
                    "values": [
                        "26.8"
                    ]
                },
                {
                    "category": "Black african",
                    "values": [
                        "23.2"
                    ]
                },
                {
                    "category": "Black caribbean",
                    "values": [
                        "31.9"
                    ]
                },
                {
                    "category": "Any other black background",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Other",
                    "values": [
                        "25.1"
                    ]
                },
                {
                    "category": "Arab",
                    "values": [
                        "21.4"
                    ]
                },
                {
                    "category": "Any other ethnic group",
                    "values": [
                        "27.3"
                    ]
                }
            ]
        },
        {
            "group": "2014/15",
            "data": [
                {
                    "category": "White",
                    "values": [
                        "17.4"
                    ]
                },
                {
                    "category": "White British",
                    "values": [
                        "17.4"
                    ]
                },
                {
                    "category": "White Irish",
                    "values": [
                        "17.5"
                    ]
                },
                {
                    "category": "Gypsy or Irish Traveller",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Any other white background",
                    "values": [
                        "18.7"
                    ]
                },
                {
                    "category": "Mixed",
                    "values": [
                        "20.3"
                    ]
                },
                {
                    "category": "Mixed white and black caribbean",
                    "values": [
                        "21.4"
                    ]
                },
                {
                    "category": "Mixed white and black african",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Mixed white and asian",
                    "values": [
                        "17.8"
                    ]
                },
                {
                    "category": "Any other Mixed/Multiple ethnic background",
                    "values": [
                        "26.8"
                    ]
                },
                {
                    "category": "Asian",
                    "values": [
                        "28.2"
                    ]
                },
                {
                    "category": "Indian",
                    "values": [
                        "29.3"
                    ]
                },
                {
                    "category": "Pakistani",
                    "values": [
                        "27.5"
                    ]
                },
                {
                    "category": "Bangladeshi",
                    "values": [
                        "29.1"
                    ]
                },
                {
                    "category": "Chinese",
                    "values": [
                        "19.3"
                    ]
                },
                {
                    "category": "Any other asian",
                    "values": [
                        "30.3"
                    ]
                },
                {
                    "category": "Black",
                    "values": [
                        "23.7"
                    ]
                },
                {
                    "category": "Black african",
                    "values": [
                        "22.2"
                    ]
                },
                {
                    "category": "Black caribbean",
                    "values": [
                        "25.7"
                    ]
                },
                {
                    "category": "Any other black background",
                    "values": [
                        "26.2"
                    ]
                },
                {
                    "category": "Other",
                    "values": [
                        "26.0"
                    ]
                },
                {
                    "category": "Arab",
                    "values": [
                        "25.5"
                    ]
                },
                {
                    "category": "Any other ethnic group",
                    "values": [
                        "26.3"
                    ]
                }
            ]
        },
        {
            "group": "2015/16",
            "data": [
                {
                    "category": "White",
                    "values": [
                        "18.0"
                    ]
                },
                {
                    "category": "White British",
                    "values": [
                        "17.8"
                    ]
                },
                {
                    "category": "White Irish",
                    "values": [
                        "20.4"
                    ]
                },
                {
                    "category": "Gypsy or Irish Traveller",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Any other white background",
                    "values": [
                        "20.7"
                    ]
                },
                {
                    "category": "Mixed",
                    "values": [
                        "21.1"
                    ]
                },
                {
                    "category": "Mixed white and black caribbean",
                    "values": [
                        "17.7"
                    ]
                },
                {
                    "category": "Mixed white and black african",
                    "values": [
                        "-"
                    ]
                },
                {
                    "category": "Mixed white and asian",
                    "values": [
                        "21.4"
                    ]
                },
                {
                    "category": "Any other Mixed/Multiple ethnic background",
                    "values": [
                        "26.3"
                    ]
                },
                {
                    "category": "Asian",
                    "values": [
                        "27.1"
                    ]
                },
                {
                    "category": "Indian",
                    "values": [
                        "27.5"
                    ]
                },
                {
                    "category": "Pakistani",
                    "values": [
                        "29.8"
                    ]
                },
                {
                    "category": "Bangladeshi",
                    "values": [
                        "31.4"
                    ]
                },
                {
                    "category": "Chinese",
                    "values": [
                        "15.7"
                    ]
                },
                {
                    "category": "Any other asian",
                    "values": [
                        "25.7"
                    ]
                },
                {
                    "category": "Black",
                    "values": [
                        "26.3"
                    ]
                },
                {
                    "category": "Black african",
                    "values": [
                        "25.4"
                    ]
                },
                {
                    "category": "Black caribbean",
                    "values": [
                        "27.7"
                    ]
                },
                {
                    "category": "Any other black background",
                    "values": [
                        "28.1"
                    ]
                },
                {
                    "category": "Other",
                    "values": [
                        "27.1"
                    ]
                },
                {
                    "category": "Arab",
                    "values": [
                        "29.7"
                    ]
                },
                {
                    "category": "Any other ethnic group",
                    "values": [
                        "25.5"
                    ]
                }
            ]
        }
    ]
}

"""
For data download builder we are going for freshly structured table objects - correct as at 27/09/2017
"""
table_source_data = {
    "data": [
        [
            "Measure",
            "Time",
            "Ethnicity",
            "Ethnicity_type",
            "Value"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "White",
            "ONS 5+1",
            "17.9"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "White British",
            "ONS 18+1",
            "17.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "White Irish",
            "ONS 18+1",
            "20.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Gypsy or Irish Traveller",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Any other white background",
            "ONS 18+1",
            "20.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Mixed",
            "ONS 5+1",
            "28.6"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Mixed white and black caribbean",
            "ONS 18+1",
            "24.9"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Mixed white and black african",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Mixed white and asian",
            "ONS 18+1",
            "32.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Any other Mixed/Multiple ethnic background",
            "ONS 18+1",
            "24.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Asian",
            "ONS 5+1",
            "31.5"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Indian",
            "ONS 18+1",
            "33.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Pakistani",
            "ONS 18+1",
            "35.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Bangladeshi",
            "ONS 18+1",
            "34.2"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Chinese",
            "ONS 18+1",
            "15.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Any other asian",
            "ONS 18+1",
            "28.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Black",
            "ONS 5+1",
            "26.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Black african",
            "ONS 18+1",
            "23.2"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Black caribbean",
            "ONS 18+1",
            "31.9"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Any other black background",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Other",
            "ONS 5+1",
            "25.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Arab",
            "ONS 18+1",
            "21.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2013/14",
            "Any other ethnic group",
            "ONS 18+1",
            "27.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "White",
            "ONS 5+1",
            "17.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "White British",
            "ONS 18+1",
            "17.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "White Irish",
            "ONS 18+1",
            "17.5"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Gypsy or Irish Traveller",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Any other white background",
            "ONS 18+1",
            "18.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Mixed",
            "ONS 5+1",
            "20.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Mixed white and black caribbean",
            "ONS 18+1",
            "21.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Mixed white and black african",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Mixed white and asian",
            "ONS 18+1",
            "17.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Any other Mixed/Multiple ethnic background",
            "ONS 18+1",
            "26.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Asian",
            "ONS 5+1",
            "28.2"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Indian",
            "ONS 18+1",
            "29.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Pakistani",
            "ONS 18+1",
            "27.5"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Bangladeshi",
            "ONS 18+1",
            "29.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Chinese",
            "ONS 18+1",
            "19.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Any other asian",
            "ONS 18+1",
            "30.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Black",
            "ONS 5+1",
            "23.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Black african",
            "ONS 18+1",
            "22.2"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Black caribbean",
            "ONS 18+1",
            "25.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Any other black background",
            "ONS 18+1",
            "26.2"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Other",
            "ONS 5+1",
            "26.0"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Arab",
            "ONS 18+1",
            "25.5"
        ],
        [
            "Proportion of adults that fear crime",
            "2014/15",
            "Any other ethnic group",
            "ONS 18+1",
            "26.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "White",
            "ONS 5+1",
            "18.0"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "White British",
            "ONS 18+1",
            "17.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "White Irish",
            "ONS 18+1",
            "20.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Gypsy or Irish Traveller",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Any other white background",
            "ONS 18+1",
            "20.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Mixed",
            "ONS 5+1",
            "21.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Mixed white and black caribbean",
            "ONS 18+1",
            "17.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Mixed white and black african",
            "ONS 18+1",
            "-"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Mixed white and asian",
            "ONS 18+1",
            "21.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Any other Mixed/Multiple ethnic background",
            "ONS 18+1",
            "26.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Asian",
            "ONS 5+1",
            "27.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Indian",
            "ONS 18+1",
            "27.5"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Pakistani",
            "ONS 18+1",
            "29.8"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Bangladeshi",
            "ONS 18+1",
            "31.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Chinese",
            "ONS 18+1",
            "15.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Any other asian",
            "ONS 18+1",
            "25.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Black",
            "ONS 5+1",
            "26.3"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Black african",
            "ONS 18+1",
            "25.4"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Black caribbean",
            "ONS 18+1",
            "27.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Any other black background",
            "ONS 18+1",
            "28.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Other",
            "ONS 5+1",
            "27.1"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Arab",
            "ONS 18+1",
            "29.7"
        ],
        [
            "Proportion of adults that fear crime",
            "2015/16",
            "Any other ethnic group",
            "ONS 18+1",
            "25.5"
        ]
    ],
    "tableOptions": {
        "table_category_column": "Ethnicity",
        "table_group_column": "Time",
        "table_column_1": "Value",
        "table_column_2": "none",
        "table_column_3": "none",
        "table_column_4": "none",
        "table_column_5": "none",
        "table_column_1_name": "%",
        "table_column_2_name": "Unweighted base",
        "table_column_3_name": "",
        "table_column_4_name": "",
        "table_column_5_name": ""
    }
}


def simple_table():
    return {
        "type": "simple",
        "parent_child": False,
        "header": "Percentage of adults with an AUDIT score of 8-15 (hazardous drinking) by ethnicity and sex",
        "subtitle": "",
        "footer": "",
        "category": "Ethnicity",
        "columns": [
            "Column1",
            "Column2"
        ],
        "data": [
            {
                "category": "White",
                "relationships": {
                    "is_parent": False,
                    "is_child": False,
                    "parent": "White"
                },
                "order": 0,
                "values": [
                    "25.6",
                    "0.256"
                ],
                "sort_values": [
                    25.6,
                    0.256
                ]
            },
            {
                "category": "Other",
                "relationships": {
                    "is_parent": False,
                    "is_child": False,
                    "parent": "Other"
                },
                "order": 1,
                "values": [
                    "16.6",
                    "0.166"
                ],
                "sort_values": [
                    16.6,
                    0.166
                ]
            }
        ],
        "category_caption": "Custom category caption"
    }


def grouped_table():
    return {
        "group_columns": [
            "",
            "Men",
            "Women"
        ],
        "type": "grouped",
        "category": "Standard Ethnicity",
        "group_column": "Sex",
        "columns": [
            "Value",
            "Rate"
        ],
        "data": [
            {
                "category": "White",
                "relationships": {
                    "is_parent": False,
                    "is_child": False,
                    "parent": "White"
                },
                "order": 0,
                "values": [
                    "25.6",
                    "0.256",
                    "12.8",
                    "0.128"
                ],
                "sort_values": [
                    25.6,
                    0.256,
                    12.8,
                    0.128
                ]
            },
            {
                "category": "Other",
                "relationships": {
                    "is_parent": False,
                    "is_child": False,
                    "parent": "Other"
                },
                "order": 1,
                "values": [
                    "16.6",
                    "0.166",
                    "10.0",
                    "0.100"
                ],
                "sort_values": [
                    16.6,
                    0.166,
                    10,
                    0.1
                ]
            }
        ],
        "header": "Percentage of adults with an AUDIT score of 8-15 (hazardous drinking) by ethnicity and sex",
        "subtitle": "",
        "footer": "",
        "groups": [
            {
                "group": "Men",
                "data": [
                    {
                        "category": "White",
                        "relationships": {
                            "is_parent": False,
                            "is_child": False,
                            "parent": "White"
                        },
                        "order": 0,
                        "values": [
                            "25.6",
                            "0.256"
                        ],
                        "sort_values": [
                            25.6,
                            0.256
                        ]
                    },
                    {
                        "category": "Other",
                        "relationships": {
                            "is_parent": False,
                            "is_child": False,
                            "parent": "Other"
                        },
                        "order": 1,
                        "values": [
                            "16.6",
                            "0.166"
                        ],
                        "sort_values": [
                            16.6,
                            0.166
                        ]
                    }
                ]
            },
            {
                "group": "Women",
                "data": [
                    {
                        "category": "White",
                        "relationships": {
                            "is_parent": False,
                            "is_child": False,
                            "parent": "White"
                        },
                        "order": 0,
                        "values": [
                            "12.8",
                            "0.128"
                        ],
                        "sort_values": [
                            12.8,
                            0.128
                        ]
                    },
                    {
                        "category": "Other",
                        "relationships": {
                            "is_parent": False,
                            "is_child": False,
                            "parent": "Other"
                        },
                        "order": 1,
                        "values": [
                            "10.0",
                            "0.100"
                        ],
                        "sort_values": [
                            10,
                            0.1
                        ]
                    }
                ]
            }
        ],
        "parent_child": False,
        "category_caption": "Custom category caption"
    }


def single_series_bar_chart():
    return {
      "type": "bar",
      "title": {
        "text": "Chart title"
      },
      "xAxis": {
        "title": {
          "text": "x-axis title"
        },
        "categories": [
          "category 1",
          "category 2"
        ]
      },
      "yAxis": {
        "title": {
          "text": ""
        }
      },
      "series": [
        {
          "name": "Ethnicity with parent",
          "data": [
            73.1,
            77.9
          ]
        }
      ],
      "number_format": {
        "multiplier": 1,
        "prefix": "",
        "suffix": "%",
        "min": 0,
        "max": 100
      }
    }


def multi_series_bar_chart():
    return {
      "type": "bar",
      "title": {
        "text": "Percentage of underoccupied households by ethnicity and socio-economic group"
      },
      "xAxis": {
        "title": {
          "text": "Percentage (%)"
        },
        "categories": [
          "Higher managerial, administrative and professional occupations",
          "Intermediate occupations",
          "Routine and manual occupations"
        ]
      },
      "yAxis": {
        "title": {
          "text": ""
        }
      },
      "series": [
        {
          "name": "White British",
          "data": [
            49,
            40,
            29
          ]
        },
        {
          "name": "All other ethnic groups",
          "data": [
            28,
            18,
            14
          ]
        }
      ],
      "number_format": {
        "multiplier": 1,
        "prefix": "",
        "suffix": "%",
        "min": 0,
        "max": 100
      }
    }
