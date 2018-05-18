function generateQRCode() {
        jQuery('div#qrCodeCurrUrl').qrcode({
        text:window.location.href
    });
}

function generateBarcode(id, num) {
    if (num == null || num == '') {
        return
    }
    JsBarcode(id, num, {format: 'EAN13'})

}
        
