/**
 * Created by Tom.Ridd on 05/05/2017.
 */

var browser = typeof bowser !== 'undefined' ? bowser :  null;

function setColour(chartObject) {
    var colours = ['#2B8CC4', '#F44336', '#4CAF50', '#FFC107', '#9C27B0', '#00BCD4'];
    return chartObject.type === 'line' ? colours : chartObject.series.length === 4 ? ['#2B8CC4', '#4891BB', '#76A6C2', '#B3CBD9'] : chartObject.series.length === 3 ? ['#2B8CC4', '#76A6C2', '#B3CBD9'] : chartObject.series.length === 2 ? ['#2B8CC4', '#B3CBD9'] : colours;
}

function setHeight(chartObject, padding) {
  var bar = chartObject.type === 'component' ? 33 : chartObject.series.length > 1 ? 30 : chartObject.type === 'small_bar' ? 40 : 33;
  var barPadding = 10;
  var seriesLength = 0;
  var padding = padding ? padding : 160;

  for ( var i = 0; i < ( chartObject.type === 'component' ? chartObject.xAxis.categories.length : chartObject.series.length); i++ ) {
    seriesLength += (chartObject.type === 'component' ? 1 : chartObject.series[i].data.length);
  }

  return ( seriesLength * bar ) + padding;
}

function drawChart(container_id, chartObject) {
    if(chartObject) {
        if (chartObject.type === 'bar') {
            return barchart(container_id, chartObject);
        } else if (chartObject.type === 'line') {
            return linechart(container_id, chartObject);
        } else if (chartObject.type === 'component') {
            return componentChart(container_id, chartObject);
        } else if (chartObject.type === 'panel_bar_chart') {
            return panelBarchart(container_id, chartObject);
        } else if (chartObject.type === 'panel_line_chart') {
            return panelLinechart(container_id, chartObject);
        }
    }
}

function barchart(container_id, chartObject) {
    adjustChartObject(chartObject);
    adjustParents(chartObject);
    setDecimalPlaces(chartObject);
    return chart = Highcharts.chart(container_id, {
        colors: setColour(chartObject),
        chart: {
            type:'bar',
            height: setHeight(chartObject)
        },
        title: {
            text: chartObject.title.text,
            style: {
              color: "black"
            }
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.yAxis.title.text
            },
            labels: browser && browser.msie && parseInt(browser.version) === 8  ?
            {
                fontSize: chartObject.series.length <= 1 ? "17px" : "14px",
                fontFamily: "nta"
            } : {
                formatter:function() {
                    return $.inArray(this.value,chartObject.parents) < 0 ? this.value : '<b>' + this.value + '</b>';
                },
                style: { textOverflow: 'none', color: "black" }
            }
        },
        yAxis: {
            title: {
                text: chartObject.xAxis.title.text
            },
            labels: {
              autoRotation: "off",
              style: {color: "black"}
            }
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: (chartObject.series.length > 1)
        },
        plotOptions: {
            bar: {
            dataLabels: {
              enabled: true,
              color: ['#000','#fff'],
              style: {
                textOutline: false,
                fontSize: chartObject.series.length <= 1 ? "17px" : "14px",
                fontFamily: "nta",
                fontWeight: "400"
              },
              formatter: function() {
                if(this.y > 0.0001) {

                    return chartObject.number_format.prefix +
                        formatNumberWithDecimalPlaces(this.y, chartObject.decimalPlaces) +
                        chartObject.number_format.suffix;
                } else {
                    if($.inArray(this.key, chartObject.parents) !== -1) {
                        return '';
                    } else {
                       return "Not enough data";
                    }
                }
              },
              rotation: 0
            }
          },
          series: {
            pointPadding: chartObject.series.length > 1 ? 0 : .075,
            groupPadding: 0.1,
            states: {
                hover: {
                    enabled: false
                }
            }
          }
        },
        tooltip: barChartTooltip(chartObject),
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });
}

function panelBarchart(container_id, chartObject) {

    var internal_divs = "<div class='small-chart-title'>" + chartObject.title.text + "</div>";
    var max = 0;

    for (var i = 0; i < chartObject.panels.length; i++) {
        for (var j = 0; j < chartObject.panels[i].series.length; j++) {
            for(var k = 0; k < chartObject.panels[i].series[j].data.length; k++) {
                max = max < chartObject.panels[i].series[j].data[k] ? chartObject.panels[i].series[j].data[k] : max ;
            }
        }
    }
    for(var c in chartObject.panels) {
        internal_divs = internal_divs + "<div id=\"" + container_id + "_" + c + "\" class=\"chart-container column-one-" + (chartObject.panels.length > 2 ? 'third' : 'half') + "\"></div>";
    }
    $('#' + container_id).html(internal_divs);

    var charts = [];
    for(c in chartObject.panels) {
        var panel_container_id = container_id + "_" + c;
        var panelChart = chartObject.panels[c];
        charts.push(smallBarchart(panel_container_id, panelChart, max));
    }
    return charts;
}

function smallBarchart(container_id, chartObject, max) {
    adjustChartObject(chartObject);
    var chart = Highcharts.chart(container_id, {
        colors: setColour(chartObject),
        chart: {
            type: 'bar',
            height: setHeight(chartObject),
            events: {
                redraw: function(e) {
                    var data = e.target.series[0].data;
                    var container = e.target.series[0].chart.container;
                    var $dataLabels = $(container).find('g.highcharts-data-labels');
                    var $xLabels = $(container).find('g.highcharts-yaxis-labels');
                    var $xLabelValue = $xLabels.find('text').last().text().replace('%', '');

                    // add precent sign to last x axis labels when table is displaying precentages
                    if (chartObject.number_format.suffix === '%') {
                        $xLabels.find('text')
                            .last()
                            .text($xLabelValue + '%');
                    }

                    // add inline styling to data labels when they are justified to the left edge of the bar
                    for (var i = 0; i < data.length; i++) {
                        if(data[i].isLabelJustified) {
                            $dataLabels.find('.highcharts-data-label')
                                .eq(i)
                                .find('text')
                                .attr('style', 'fill: #fff;');
                        }
                        else {
                            $dataLabels.find('.highcharts-data-label')
                                .eq(i)
                                .find('text')
                                .attr('style', 'fill: #000;');
                        }
                    }
                    e.target.render();
                }
            }
        },
        title: {
            text: chartObject.title.text
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            labels: {
                items: {
                    style: {
                        left: '100px'
                    }
                },
                style: {
                    textOverflow: 'none',
                    color: 'black',
                    fontSize: '16px'
                },
                y: 5
            }
        },
        yAxis: {
            max: max,
            title: {
                text: ""
            }
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: (chartObject.series.length > 1)
        },
        plotOptions: {
            bar: {
                dataLabels: {
                    enabled: true,
                    color: ['#000','#fff'],
                    verticalAlign: 'middle',
                    y: 3,
                    style: {
                        textOutline: false,
                        fontSize: chartObject.series.length <= 1 ? "17px" : "14px",
                        fontFamily: "nta",
                        fontWeight: "400"
                    },
                    formatter: function() {
                        return this.y > 0.0001 ? formatNumberWithDecimalPlaces(this.y, chartObject.decimalPlaces) + '' + (chartObject.number_format.suffix === '%' ? '%' : '') : 'Not enough data';
                    },
                    rotation: 0
                },
                borderWidth: 0
            },
            series: {
                pointPadding: chartObject.series.length > 1 ? 0 : .075,
                groupPadding: 0.1,
                states: {
                    hover: {
                        enabled: false
                    }
                }
            }
        },
        tooltip: barChartTooltip(chartObject),
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });

    chart.redraw();

    return chart;
}


function panelLinechart(container_id, chartObject) {

    var internal_divs = "<div class='small-chart-title'>" + chartObject.title.text + "</div>";
    var max = 0, min = 0;

    for (var i = 0; i < chartObject.panels.length; i++) {
        for (var j = 0; j < chartObject.panels[i].series.length; j++) {
            for(var k = 0; k < chartObject.panels[i].series[j].data.length; k++) {
                max = max < chartObject.panels[i].series[j].data[k] ? chartObject.panels[i].series[j].data[k] : max ;
            }
        }
    }

    min = max;

    for (var i = 0; i < chartObject.panels.length; i++) {
        for (var j = 0; j < chartObject.panels[i].series.length; j++) {
            for(var k = 0; k < chartObject.panels[i].series[j].data.length; k++) {
                min = chartObject.panels[i].series[j].data[k] < min ? chartObject.panels[i].series[j].data[k] : min ;
            }
        }
    }

    for(var c in chartObject.panels) {
        internal_divs = internal_divs + "<div id=\"" + container_id + "_" + c + "\" class=\"chart-container column-one-"+ (chartObject.panels.length > 2 ? 'third' : 'half') +"\"></div>";
    }
    $('#' + container_id).addClass('panel-line-chart').html(internal_divs);

    var charts = [];
    for(c in chartObject.panels) {
        var panel_container_id = container_id + "_" + c;
        var panelChart = chartObject.panels[c];
        charts.push(smallLinechart(panel_container_id, panelChart, max,  min));
    };
    return charts;
}

function smallLinechart(container_id, chartObject, max, min) {
    adjustChartObject(chartObject);
    var yaxis = {
        title: {
            text: chartObject.yAxis.title.text
        },
        labels: {
            format: chartObject.number_format.prefix + decimalPointFormat('value', chartObject.decimalPlaces) + chartObject.number_format.suffix,
            style: {
                fontSize: '16px',
                color: 'black'
            }
        },
        max: max,
        min: min
    };

    for(var i = 0; i < chartObject.series.length; i++) {
        chartObject.series[i].marker = { symbol: 'circle' };
    }

    if(chartObject.number_format.min !== '') {
        yaxis['min'] = chartObject.number_format.min;
    }
    if(chartObject.number_format.max !== '') {
        yaxis['max'] = chartObject.number_format.max;
    }

    var chart = Highcharts.chart(container_id, {
        chart: {
            marginTop: 20,
            height: 250
        },
        colors: setColour(chartObject),
        title: {
            text: chartObject.title.text,
            useHTML: true
        },
        legend: {
            enabled: false
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.xAxis.title.text
            },
            labels: {
                formatter: function() {
                    this.axis.labelRotation = 0;
                    if(this.isFirst) {
                        this.axis.labelAlign = 'left';
                        return this.value;
                    }
                    else if(this.isLast) {
                        this.axis.labelAlign = 'right';
                        return this.value;
                    }
                },
                style: { fontSize: '12px'},
                useHTML: true
            }
        },
        yAxis: yaxis,
        tooltip: lineChartTooltip(chartObject),
        credits: {
            enabled: false
        },
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });

    return chart;
}

function barChartTooltip(chartObject) {
    if(chartObject.series.length > 1)
    {
        return { pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>'
        + chartObject.number_format.prefix
        + decimalPointFormat('point.y', chartObject.decimalPlaces)
        + chartObject.number_format.suffix + '</b><br/>' }
    } else {
        return { pointFormat: '<span style="color:{point.color}">\u25CF</span><b>'
        + chartObject.number_format.prefix
        + decimalPointFormat('point.y', chartObject.decimalPlaces)
        + chartObject.number_format.suffix + '</b><br/>'}
    }
}

function linechart(container_id, chartObject) {
    adjustChartObject(chartObject);
    setDecimalPlaces(chartObject);

    var yaxis = {
        title: {
            text: chartObject.yAxis.title.text
        },
        labels: {
            format: chartObject.number_format.prefix + decimalPointFormat('value', chartObject.decimalPlaces) + chartObject.number_format.suffix
        }
    };

    for(var i = 0; i < chartObject.series.length; i++) {
        chartObject.series[i].marker = { symbol: 'circle' };
    }

    if(chartObject.number_format.min !== '') {
        yaxis['min'] = chartObject.number_format.min;
    }
    if(chartObject.number_format.max !== '') {
        yaxis['max'] = chartObject.number_format.max;
    }

    return Highcharts.chart(container_id, {
        chart: {
            marginTop: 20,
            height: 400
        },
        colors: setColour(chartObject),
        title: {
            text: chartObject.title.text
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.xAxis.title.text
            }
        },
        yAxis: yaxis,
        tooltip: lineChartTooltip(chartObject),
        credits: {
            enabled: false
        },
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });}


function lineChartTooltip(chartObject) {

    return {
        pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>'
            + chartObject.number_format.prefix
            + decimalPointFormat('point.y', chartObject.decimalPlaces)
            + chartObject.number_format.suffix + '</b><br/>',
        formatter: function() { return '<span class="first">' + this.x + '</span><br><span class="last">' + this.series.name + ': ' + this.y + '</span>' },
        useHTML: true
     }
}

function decimalPointFormat(label, dp) {
    if(dp && dp > 0) {
        return '{' + label + ':.' + dp + 'f}';
    }
    return '{' + label + '}';
}

function componentChart(container_id, chartObject) {
    adjustChartObject(chartObject);
    setDecimalPlaces(chartObject);

    return Highcharts.chart(container_id, {
        chart: {
            type:'bar',
            height: setHeight(chartObject)
        },
        colors: setColour(chartObject),
        title: {
            text:  chartObject.title.text
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.xAxis.title.text
            }
        },
        yAxis: {
            title: {
                text: chartObject.yAxis.title.text
            },
            min: 0,
            max: 100
        },
        legend: {
            reversed: true
        },
        plotOptions: {
            series: {
                stacking: 'normal',
                pointPadding: chartObject.series.length > 1 ? 0 : .075,
                groupPadding: 0.1
            }
        },
        tooltip: barChartTooltip(chartObject),
        credits: {
            enabled: false
        },
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });}

    function adjustChartObject(chartObject) {
        var multiplier = chartObject.number_format.multiplier;
        if(multiplier !== 1.0) {
            for(var s in chartObject.series) {
                for(var d in chartObject.series[s].data) {
                    var value = (multiplier * chartObject.series[s].data[d]);
                    chartObject.series[s].data[d] = Math.round(value * 100)/100;
                }
            }
        }
    }

    function adjustParents(chartObject) {
        if(chartObject.parent_child) {
            _.forEach(chartObject.series, function(series) {

                // for all existing data points make sure we mark them include
                _.forEach(series.data, function(item) {
                    item['include'] = true;
                });

                // get a big list of parents
                var presentParents = _.filter(series.data, function(item) { item.relationships.is_parent; });
                var missingParents = getMissingCategories(chartObject.parents, series);

                var parentDict = {};
                _.forEach(presentParents, function(item) { parentDict[item.category] = item; });
                _.forEach(missingParents, function(item) { parentDict[item.category] = item; });

                var currentParent = {category:'null'};
                var fullSeriesData = [];
                _.forEach(series.data, function(item) {
                    if(item.relationships.is_parent) {
                        fullSeriesData.push(item);

                        currentParent = item;
                    } else if(currentParent.category == item.relationships.parent) {
                        fullSeriesData.push(item);
                    } else {
                        fullSeriesData.push(parentDict[item.relationships.parent]);
                        fullSeriesData.push(item);

                        currentParent = parentDict[item.relationships.parent];
                    }
                });
                series.data = fullSeriesData;

                // WARNING Strictly speaking we need a better version for this
                chartObject.xAxis.categories = _.map(series.data, function(item) { return item.category ;});
            })
        }
    }

    function getMissingCategories(categoryList, pointList) {
        var missingCategories = [];
        var pointCategories = _.uniq(_.map(pointList, function(item) { return item.category;}));
        _.forEach(categoryList, function(category) {
            if($.inArray(category, pointCategories) == -1) {
                // WARNING - Parent colour hardcoded
                missingCategories.push( {
                    y: 0,
                    relationships: {is_parent: true, is_child: false, parent: parent},
                    category: category,
                    color: '#2B8CC4',
                    include: false
                });
            };
        });
        return missingCategories;
    }

    function setDecimalPlaces(chartObject) {
        var values = _.flatten(_.map(chartObject.series, function (series) { return series.data }));
        chartObject.decimalPlaces = seriesDecimalPlaces(values);
    }
