async function initPlaid(){
    const linkHandler = Plaid.create({
      env: 'sandbox',
      token: await $.post('/plaid/get_link_token/'),
      onSuccess: (public_token, metadata) => {
        // Send the public_token to your app server.
        console.log("public_token is - ", public_token)
        $.post('plaid/get_access_token/', {
          public_token: 'link-sandbox-0503eac0-440c-4925-be1f-146d23737952',
        });
      },
      onExit: (err, metadata) => {
        // Optionally capture when your user exited the Link flow.
        // Storing this information can be helpful for support.
      },
      onEvent: (eventName, metadata) => {
        console.log("eventName is - ", eventName)
        // Optionally capture Link flow events, streamed through
        // this callback as your users connect an Item to Plaid.
      },
    });
    linkHandler.open();
}

//document.getElementById('plaidLink').onClick = initPlaid;


