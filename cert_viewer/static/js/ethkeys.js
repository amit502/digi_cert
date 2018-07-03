$(document).ready(function () {
    var clipboard = new Clipboard('#copy-btn');

    jQuery( '#copy-btn' ).ready(function( ) {
        $('.hasTooltip').tooltip({'trigger': 'click', delay: {"show": 500, "hide": 100}});
    });

    $("#generatekeys").click(function () {

        $(".show-later").hide();
        //var keyPair = ethereumjs.ECPair.makeRandom();
       /* if (typeof web3 !== 'undefined') {
            web3 = new Web3(web3.currentProvider);
        } else {
            // set the provider you want from Web3.providers
            web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));
        }
        var batch = web3.createBatch();
        batch.add(web3.personal.newAccount('latest', callback));
        batch.execute();
        var account=web3.personal.newAccount();
        //$('#privKey').text(keyPair.toWIF());
       // $('#pubKey').text(keyPair.getAddress());
       var keyPair=JSON.parse(account);*/

       var keyPair = ethers.Wallet.createRandom();
       
       $('#privKey').text(keyPair.privateKey);

       $('#pubKey').text(keyPair.address);
        $(".enable-clear").html("");

        var qrcode1 = new QRCode(document.getElementById("pubKeyQr"), {
            text: keyPair.address,
            width: 70,
            height: 70,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
        var qrcode2 = new QRCode(document.getElementById("privKeyQr"), {
            text: keyPair.privateKey,
            width: 60,
            height: 60,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });

        $("#to-load").show();
        $("#to-load").Loadingdotdotdot({
            "speed": 400,
            "maxDots": 4,
            "word": "Loading"
        });

        setTimeout(
            function () {
                $(".show-later").show();
                $("#return-link").attr('href', '/request?identity=true&address=' + keyPair.getAddress());
                $("#to-load").Loadingdotdotdot("Stop");
                $("#to-load").hide();
            }, 5000);

    });

});