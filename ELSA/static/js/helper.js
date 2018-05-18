function generateQRCode() {
        jQuery('div#qrCodeCurrUrl').qrcode({
        text:window.location.href
    });
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
        
