<!DOCTYPE html>
<html>
<head>
    <title>Piratenlogin</title>

    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="robots" content="noindex, nofollow">

    <link rel="shortcut icon" href="${resourcesPath}/img/favicon.ico" />

    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link href="${resourcesCommonPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
</head>

<body>
<div class="container-fluid">
  <div class="row">
    <div class="col-sm-10 col-sm-offset-1 col-md-8 col-md-offset-2 col-lg-8 col-lg-offset-2">
      <div class="welcome-header">
        <img src="${resourcesPath}/logo.png" alt="${productName}" border="0" />
        <h1>Willkommen beim <strong>Piratenlogin</strong></h1>
      </div>
      <div class="row">
        <div class="col-xs-12 col-sm-4">
          <div class="card-pf h-l">
            <#if successMessage?has_content>
                <p class="alert success">${successMessage}</p>
            <#elseif errorMessage?has_content>
                <p class="alert error">${errorMessage}</p>
                <h3><img src="welcome-content/user.png">Account verwalten</h3>
            </#if>
            <div class="welcome-primary-link">
              <h3><a href="/auth/realms/Piratenlogin/account"><img src="welcome-content/user.png">Account verwalten <i class="fa fa-angle-right link" aria-hidden="true"></i></a></h3>
              <div class="description">
                Verwalte deine Zugangsdaten und autorisierten Anwendungen.
              </div>
            </div>
          </div>
        </div>
        <div class="col-xs-12 col-sm-4">
          <div class="card-pf h-m less-padding">
            <h3><img class="doc-img" src="welcome-content/admin-console.png">Anwendungen</h3>
            mit unterstütztem Piratenlogin:
          </div>
          <div class="card-pf h-m less-padding">
            <h3><a href="https://forum.piratenpartei.de">Forum <i class="fa fa-angle-right link" aria-hidden="true"></i></a></h3>
            Für existierende Accounts siehe <a href="https://forum.piratenpartei.de/t/anleitung-piratenlogin-fuer-das-forum/5704/2">diese Anleitung</a>.
          </div>
          <div class="card-pf h-m">
            <h3><a href="https://antrag.piratenpartei.de">Antragsportal <i class="fa fa-angle-right link" aria-hidden="true"></i></a></h3>
          </div>
        </div>
        <div class="col-xs-12 col-sm-4">
          <div class="card-pf h-m">
            <h3><a href="mailto:support@it.piratenpartei.de"><img src="welcome-content/mail.png">Support - support@it.piratenpartei.de <i class="fa fa-angle-right link" aria-hidden="true"></i></a></h3>
          </div>
        </div>
      </div>
      <div class='footer'>
      </div>
    </div>
  </div>
</div>
</body>
</html>
