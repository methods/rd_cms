function TableWithFixedHeader(outerTableElement) {

  var outerTableElement = outerTableElement
  var middleTableElement, innerTableElement, tableContainer,
    tableElement, fixedTable, tableHeader, fixedTableContainer

  function setup() {

    if (outerTableElement) {
      middleTableElement = outerTableElement.querySelector('.table-container-middle')
      innerTableElement = outerTableElement.querySelector('.table-container-inner')
      tableContainer = outerTableElement.querySelector('.table-container')
      tableElement = outerTableElement.querySelector('table')

      if (tableContainer) {

        tableHeader = tableElement.querySelector('thead')

        var fixedTableHeader = tableHeader.cloneNode(true)
        fixedTableHeader.classList.add('fixed')

        fixedTable = document.createElement('table')
        fixedTable.setAttribute('class', tableElement.getAttribute('class') + ' fixed')
        fixedTable.classList.remove('fixed-headers')

        fixedTable.appendChild(fixedTableHeader)

        fixedTableContainer = document.createElement('div')
        fixedTableContainer.classList.add('fixed-header-container')

        fixedTableContainer.appendChild(fixedTable)

        innerTableElement.appendChild(fixedTableContainer)

        /* Update again after 200ms. Solves a few weird issues. */
        setTimeout(updatePositioning, 200)

      }
    }
  }

  function updatePositioning() {

    var height = heightForElement(tableHeader);

    tableElement.style.marginTop = '-' + height;
    innerTableElement.style.paddingTop = height;

    var mainTableHeaderCells = tableElement.querySelectorAll('thead th, thead td')
    var headerCells = fixedTable.querySelectorAll('thead th, thead td')

    var tableWidth = 0

    fixedTableContainer.style.width = '100000px'

    for (var i = 0; i < mainTableHeaderCells.length; i++) {
      headerCells[i].style.width = widthForElement(mainTableHeaderCells[i])
    };


    fixedTableContainer.style.width = widthForElement(fixedTable)
    tableElement.style.width = widthForElement(fixedTable)
    tableContainer.style.width = widthForElement(fixedTable)


    if (widthForElement(fixedTable) != widthForElement(tableElement)) {
      tableContainer.style.width = (parseFloat(widthForElement(fixedTable)) + 20) + 'px'
    }

  }

  function heightForElement(element) {

    var height;

    if (typeof window.getComputedStyle === "function") {
      height = getComputedStyle(element).height
    }

    if (!height || height == 'auto') {
      height = (element.getBoundingClientRect().bottom - element.getBoundingClientRect().top) + 'px';
    }

    return height;
  }

  function widthForElement(element) {

    if (typeof window.getComputedStyle === "function") {
      return getComputedStyle(element).width
    } else {
      return element.getBoundingClientRect().right - element.getBoundingClientRect().left;
    }

  }

  // Check for required APIs
  if (
    document.querySelector &&
    document.body.classList
  ) {
    setup()
  }


}
