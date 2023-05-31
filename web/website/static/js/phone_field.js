function setPhoneField(elID) {
    const wtf_phone_field = document.querySelector(`#${elID}`);
    wtf_phone_field.style.position = 'absolute';
    wtf_phone_field.style.top = '-9999px';
    wtf_phone_field.style.left = '-9999px';
    wtf_phone_field.parentElement.insertAdjacentHTML('beforebegin', `<div><input type="tel" id="_${elID}"></div>`);
    const fancy_phone_field = document.querySelector(`#_${elID}`);
    fancy_phone_field.classList.add('form-control');
    const fancy_phone_iti = window.intlTelInput(fancy_phone_field, {
        separateDialCode: true,
        preferredCountries: ['ru'],
        utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.21/js/utils.js",
    });
    fancy_phone_iti.setNumber(wtf_phone_field.value);
    fancy_phone_field.addEventListener('blur', function () {
        wtf_phone_field.value = fancy_phone_iti.getNumber();
    });
}

setPhoneField('phone')
setPhoneField('viber')
setPhoneField('whatsapp')