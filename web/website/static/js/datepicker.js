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

const multiSelect = document.querySelector('#multiselect');
const timePicker = document.querySelector('#timepicker');
const timeSelector = document.createElement('select');
timeSelector.classList.add('form-control', 'timeselector');
timePicker.insertAdjacentElement('afterend', timeSelector);
timeSelector.hidden = true;



function retrieveServices() {
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

function showEntries(data) {

    if (!data.results.length) {
        timePicker.hidden = false;
        timeSelector.hidden = true;
    } else {
        const services = retrieveServices();
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
            const lastEntryEnd = new Date(entryArray[entryArray.length - 1].ending_time * 1000 + adjDuration);
            const lastEntryHours = lastEntryEnd.getHours().toString().padStart(2, '0');
            const lastEntryMinutes = lastEntryEnd.getMinutes().toString().padStart(2, '0');
            for (let index = 0; index < entryArray.length; index++) {
                if (entryArray.length === 1 && secondsBefore < adjDuration && secondsAfter <= 0) {
                    console.log('No time available');
                    break;
                }
                const entryStart = new Date(entryArray[index].timestamp * 1000);
                const entryStartHours = entryStart.getHours();
                const entryStartMinutes = entryStart.getMinutes();
                const entryEnd = new Date(entryArray[index].ending_time * 1000);
                const entryEndHours = entryEnd.getHours();
                const entryEndMinutes = entryEnd.getMinutes();
                const prevEntryEnd = new Date(entryArray[index - 1]?.ending_time * 1000);
                const prevHours = prevEntryEnd.getHours().toString().padStart(2, '0');
                const prevMinutes = prevEntryEnd.getMinutes().toString().padStart(2, '0');
                if (index === 0) { // edge case: first entry
                    if (secondsBefore >= adjDuration) {
                        nIntervals = (secondsBefore - adjDuration) / 1800;
                        for (let i = 0; i < nIntervals; i++) {
                            //console.log(new Date())
                        }
                        console.log(`8:00-${entryStartHours.toString().padStart(2, '0')}:${entryStartMinutes.toString().padStart(2, '0')}`)
                    }
                    if (entryArray.length === 1) {
                        if (secondsAfter >= adjDuration) {
                            console.log(`${entryEndHours.toString().padStart(2, '0')}:${entryEndMinutes.toString().padStart(2, '0')}-20:00`);
                        } else if (secondsAfter > 0 && secondsAfter < adjDuration) {
                            console.log(`${entryEndHours.toString().padStart(2, '0')}:${entryEndMinutes.toString().padStart(2, '0')}-${lastEntryHours}:${lastEntryMinutes}`);
                        }
                    }
                } else if (index === entryArray.length - 1) { // edge case: last entry
                    if (entryStart - prevEntryEnd >= adjDuration) {
                        console.log(`${prevHours}:${prevMinutes}-${entryStartHours.toString().padStart(2, '0')}:${entryStartMinutes.toString().padStart(2, '0')}`);
                    }
                    if (secondsAfter >= adjDuration) {
                        console.log(`${entryEndHours.toString().padStart(2, '0')}:${entryEndMinutes.toString().padStart(2, '0')}-20:00`);
                    } else if (secondsAfter > 0 && secondsAfter < adjDuration) {
                        console.log(`${entryEndHours.toString().padStart(2, '0')}:${entryEndMinutes.toString().padStart(2, '0')}-${lastEntryHours}:${lastEntryMinutes}`);
                    }
                } else if (entryStart - prevEntryEnd >= adjDuration) {
                    console.log(`${prevHours}:${prevMinutes}-${entryStartHours.toString().padStart(2, '0')}:${entryStartMinutes.toString().padStart(2, '0')}`);
                }
            }
            //next code here
        });
    }
}
