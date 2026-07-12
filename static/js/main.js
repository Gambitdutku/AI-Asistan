(function ($) {
    "use strict";

    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();

    // oturum kimliğ localStorage'da tutuyoruz
    function getSessionId() {
        let sid = localStorage.getItem('asistan_session_id');
        if (!sid) {
            sid = 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 10);
            localStorage.setItem('asistan_session_id', sid);
        }
        return sid;
    }

    const sessionId = getSessionId();

    $(document).ready(function() {
        fetchAppointments();
    });

    $('#refresh-calendar').click(function() {
        fetchAppointments();
    });

    function fetchAppointments() {
        const listContainer = $('#appointment-list');
        listContainer.html('<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div></div>');

        $.ajax({
            url: '/api/appointments',
            method: 'GET',
            success: function(data) {
                listContainer.empty();
                if(data.length === 0) {
                    listContainer.html('<div class="text-muted text-center p-4">Kayıtlı randevu bulunamadı.</div>');
                    return;
                }

                data.forEach(function(app) {
                    let dateObj = new Date(app.start_time);
                    let formattedDate = dateObj.toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute:'2-digit' });

                    let customerInfo = app.customer ?
                        `<div class="small text-secondary mt-1">
                            <i class="fa fa-user me-1"></i> ${app.customer.name}
                            ${app.customer.phone ? `| <i class="fa fa-phone me-1"></i> ${app.customer.phone}` : ''}
                         </div>` : '<div class="small text-muted mt-1"><i class="fa fa-user-secret me-1"></i> Müşteri Eşleşmedi</div>';

                    let cardHtml = `
                        <div class="appointment-card bg-light p-3 mb-3 rounded">
                            <div class="d-flex justify-content-between align-items-start">
                                <h6 class="mb-1 text-dark fw-bold">${app.title}</h6>
                                <span class="badge bg-primary text-white">${formattedDate}</span>
                            </div>
                            <p class="mb-1 small text-muted">${app.description || 'Açıklama yok'}</p>
                            ${customerInfo}
                        </div>
                    `;
                    listContainer.append(cardHtml);
                });
            },
            error: function() {
                listContainer.html('<div class="text-danger text-center p-4">Veriler yüklenirken hata oluştu.</div>');
            }
        });
    }


    $('#send-btn').click(function() {
        sendMessage();
    });

    $('#user-input').keypress(function(e) {
        if(e.which == 13) {
            sendMessage();
        }
    });

    function sendMessage() {
        const inputField = $('#user-input');
        const query = inputField.val().trim();
        if(!query) return;

        $('#chat-box').append(`
            <div class="message user-msg mb-3 p-3 bg-primary text-white rounded text-end ms-auto" style="max-width: 80%;">
                <strong>Sen:</strong> ${query}
            </div>
        `);
        inputField.val('');
        $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);


        $.ajax({
            url: '/api/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ session_id: sessionId, message: query }),
            success: function(response) {
                $('#chat-box').append(`
                    <div class="message assistant-msg mb-3 p-3 bg-light rounded text-start" style="max-width: 80%;">
                        <strong>Asistan:</strong> ${response.response}
                    </div>
                `);
                $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);


                fetchAppointments();
            },
            error: function() {
                $('#chat-box').append(`
                    <div class="message text-danger mb-3 small">
                        Sistem hatası: Ajanla bağlantı kurulamadı.
                    </div>
                `);
            }
        });
    }

})(jQuery);