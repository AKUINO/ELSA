function isEmpty(el) {
    return !$.trim(el.html())
}

function generateBarcode(id, num) {
    if (num == null || num == '') {
        return false
    }
    try {
        JsBarcode(id, num, {format: 'EAN13'})
    }
    catch(err) {
        return false
    }
    return true
}
        
