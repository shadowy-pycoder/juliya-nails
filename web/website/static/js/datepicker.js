const timePicker = document.querySelector('#timepicker');
const timeSelector = document.createElement('select');
timeSelector.classList.add('form-control', 'timeselector');
timePicker.insertAdjacentElement('afterend', timeSelector);
timeSelector.hidden = true;


flatpickr("#timepicker", {
    enableTime: true,
    noCalendar: true,
    dateFormat: "H:i",
    time_24hr: true,
    defaultDate: "8:00",
    minTime: "8:00",
    maxTime: "20:00",
    minuteIncrement: 30,

});

flatpickr("#datepicker", {
    altInput: true,
    altFormat: "F j, Y",
    dateFormat: "Y-m-d",
    defaultDate: "today",
    minDate: "today",
    showMonths: 2,
    onChange: function (selectedDates, dateStr, instance) {
        getEntries(instance.element.value).then(result => showEntries(result));
    }
});
$('#multiselect').select2({
    theme: "bootstrap-5",
    width: $(this).data('width') ? $(this).data('width') : $(this).hasClass('w-100') ? '100%' : 'style',
    placeholder: $(this).data('placeholder'),
    closeOnSelect: false,
    tags: true,
    allowClear: true,
});

$('#multiselect').on('change', () => {
    const datePicker = document.querySelector('#datepicker');
    getEntries(datePicker.value).then(result => showEntries(result));
});


function retrieveServices() {
    const multiSelect = document.querySelector('#multiselect');
    const selected = Array.from(multiSelect.options)
        .filter(option => option.selected)
        .map(option => option.value);
    return selected;
}

async function getEntries(date) {
    const response = await fetch(`/api/v1/entries?date=${date}&sort=time`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

async function getServicesDuration(idArray) {
    const duration = [];
    const response = await fetch('/api/v1/services?fields=id,duration', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    const services = await response.json();
    for (let service of services.results) {
        if (idArray.includes((service.id).toString())) {
            duration.push(parseFloat(service.duration));
        }
    }
    return duration.reduce((a, b) => a + b, 0);
}

function generateOption(startDate, adjDuration) {
    startHours = startDate.getHours().toString().padStart(2, '0');
    startMinutes = startDate.getMinutes().toString().padStart(2, '0');
    endDate = new Date(startDate.getTime() + adjDuration);
    endHours = endDate.getHours().toString().padStart(2, '0');
    endMinutes = endDate.getMinutes().toString().padStart(2, '0');
    return [`${startHours}:${startMinutes}`, `${endHours}:${endMinutes}`];
}

function showEntries(data) {
    if (!data.results.length) {
        timePicker.hidden = false;
        timeSelector.hidden = true;
    } else {
        const services = retrieveServices();
        if (!services.length) {
            return;
        }
        timeSelector.hidden = false;
        timePicker.hidden = true;
        let option = null;
        getServicesDuration(services).then(result => {
            const entryArray = data.results.map((x) => x);
            const entriesDate = entryArray[0].date;
            const startDay = new Date(entriesDate).setHours(8, 0); // start of the day in milliseconds
            const endDay = new Date(entriesDate).setHours(20, 0); // end of the day in milliseconds
            const secondsBefore = new Date(entryArray[0].timestamp * 1000) - startDay; // number of milliseconds before the very first entry
            const secondsAfter = endDay - new Date(entryArray[entryArray.length - 1].ending_time * 1000);
            const adjDuration = result * 3600 * 1000; // convert duration to milliseconds
            let nIntervals = null;
            let startDate = null;
            let startTime = null;
            let endTime = null;
            for (let index = 0; index < entryArray.length; index++) {
                if (entryArray.length === 1 && secondsBefore < adjDuration && secondsAfter <= 0) {
                    console.log('No time available');
                    break;
                }
                const entryStart = new Date(entryArray[index].timestamp * 1000);
                const prevEntryEnd = new Date(entryArray[index - 1]?.ending_time * 1000);

                if (index === 0) { // edge case: first entry
                    if (secondsBefore >= adjDuration) {
                        nIntervals = (secondsBefore - adjDuration) / 1800 / 1000 + 1;
                        for (let i = 0; i < nIntervals; i++) {
                            startDate = new Date(startDay + 1800 * 1000 * i);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            console.log(`${startTime}-${endTime}`);
                        }
                    }
                    if (entryArray.length === 1) {
                        if (secondsAfter >= adjDuration) {
                            nIntervals = (secondsAfter - adjDuration) / 1800 / 1000 + 1;
                            for (let i = 0; i < nIntervals; i++) {
                                startDate = new Date((entryArray[index].ending_time + 1800 * i) * 1000);
                                [startTime, endTime] = generateOption(startDate, adjDuration);
                                console.log(`${startTime}-${endTime}`);
                            }
                        } else if (secondsAfter > 0 && secondsAfter < adjDuration) {
                            startDate = new Date(entryArray[index].ending_time * 1000);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            console.log(`${startTime}-${endTime}`);
                        }
                    }
                } else if (index === entryArray.length - 1) { // edge case: last entry
                    if (entryStart - prevEntryEnd >= adjDuration) {
                        nIntervals = (entryStart - prevEntryEnd - adjDuration) / 1800 / 1000 + 1;
                        for (let i = 0; i < nIntervals; i++) {
                            startDate = new Date((entryArray[index - 1].ending_time + 1800 * i) * 1000);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            console.log(`${startTime}-${endTime}`);
                        }
                    }
                    if (secondsAfter >= adjDuration) {
                        nIntervals = (secondsAfter - adjDuration) / 1800 / 1000 + 1;
                        for (let i = 0; i < nIntervals; i++) {
                            startDate = new Date((entryArray[index].ending_time + 1800 * i) * 1000);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            console.log(`${startTime}-${endTime}`);
                        }
                    } else if (secondsAfter > 0 && secondsAfter < adjDuration) {
                        startDate = new Date(entryArray[index].ending_time * 1000);
                        [startTime, endTime] = generateOption(startDate, adjDuration);
                        console.log(`${startTime}-${endTime}`);
                    }
                } else if (entryStart - prevEntryEnd >= adjDuration) {
                    nIntervals = (entryStart - prevEntryEnd - adjDuration) / 1800 / 1000 + 1;
                    for (let i = 0; i < nIntervals; i++) {
                        startDate = new Date((entryArray[index - 1].ending_time + 1800 * i) * 1000);
                        [startTime, endTime] = generateOption(startDate, adjDuration);
                        console.log(`${startTime}-${endTime}`);
                    }
                }
            }
            //next code here
        });
    }
}
