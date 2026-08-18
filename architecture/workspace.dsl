workspace "TrustSender.io Public Architecture" "Canonical, sanitized C4 model for the public TrustSender.io engineering portfolio." {
    model {
        customer = person "Customer" "Uses TrustSender.io to submit email lists, monitor validation jobs, and download validation reports."
        platformOperator = person "Platform Operator" "Operates, supports, and administers the platform through approved interfaces."

        googleIdentity = softwareSystem "Google Identity" "External identity provider for federated authentication." "External"
        microsoftIdentity = softwareSystem "Microsoft Identity" "External identity provider for federated authentication." "External"
        stripe = softwareSystem "Stripe" "Provides hosted checkout and signed payment events." "External"
        brevo = softwareSystem "Brevo" "Provides transactional and operational email delivery." "External"
        githubActions = softwareSystem "GitHub Actions" "Provides reviewed CI/CD and deployment automation." "External"
        internetMail = softwareSystem "Internet Mail Infrastructure" "Represents public DNS, MX infrastructure, and recipient mail servers used by validation stages." "External"

        trustSender = softwareSystem "TrustSender.io" "Public email-list validation platform for managed validation jobs and reports." {
            edge = container "Edge and Routing" "Terminates public web traffic and routes requests to the application, API, and editorial blog." "OpenLiteSpeed" "Operational,Edge"
            webApplication = container "Web Application" "Provides public, authenticated, billing, job-management, reporting, and administrative user interfaces." "Next.js" "Operational"
            applicationApi = container "Application API" "Owns application authentication, authorization, billing coordination, user-scoped job operations, and API contracts." "Python, FastAPI" "Operational"
            database = container "PostgreSQL Database" "Stores authoritative identity, session, billing, licensing, job-lifecycle, worker, event, and operational metadata." "PostgreSQL" "Operational,Data Store"
            jobControl = container "Job Control Plane" "Coordinates job lifecycle, worker selection, leases, attempts, progress, cancellation, and terminal processing." "Python, systemd orchestration" "Operational"
            p1Workers = container "Distributed P1 Worker Plane" "Executes the current distributed P1 validation engine and returns validation evidence and report artifacts to the control plane." "Python, distributed workers" "Operational"
            p2Smtp = container "P2 SMTP Execution Plane" "Status: ONGOING. Will execute conservative SMTP recipient-handshake stages for eligible recipients and return typed evidence to the central control plane." "Python, isolated SMTP workers" "Ongoing"
            blog = container "WordPress Blog" "Provides editorial content under the blog route and remains isolated from application authority." "WordPress" "Operational,Editorial"
        }

        customer -> trustSender "Uses to validate email lists and review reports" "" "Operational"
        platformOperator -> trustSender "Operates and supports through approved interfaces" "" "Operational"
        trustSender -> googleIdentity "Uses for federated authentication" "" "Operational"
        trustSender -> microsoftIdentity "Uses for federated authentication" "" "Operational"
        trustSender -> stripe "Uses for hosted checkout and signed payment events" "" "Operational"
        trustSender -> brevo "Uses for transactional and operational email delivery" "" "Operational"
        trustSender -> internetMail "Interacts with for email-validation evidence" "" "Operational"
        githubActions -> trustSender "Builds and deploys reviewed releases" "" "Operational"

        customer -> edge "Accesses" "HTTPS" "Operational"
        platformOperator -> edge "Accesses approved operational interfaces through" "HTTPS" "Operational"
        edge -> webApplication "Routes application traffic to" "HTTPS" "Operational"
        edge -> applicationApi "Routes API traffic to" "HTTPS" "Operational"
        edge -> blog "Routes blog traffic to" "HTTPS" "Operational"
        webApplication -> applicationApi "Uses" "HTTPS and JSON" "Operational"
        applicationApi -> database "Reads and writes authoritative application data in" "" "Operational"
        applicationApi -> googleIdentity "Uses for federated authentication" "" "Operational"
        applicationApi -> microsoftIdentity "Uses for federated authentication" "" "Operational"
        applicationApi -> stripe "Coordinates checkout and signed payment events with" "" "Operational"
        applicationApi -> brevo "Requests transactional and operational email through" "" "Operational"
        applicationApi -> jobControl "Submits and manages jobs through" "" "Operational"
        jobControl -> database "Reads and writes lifecycle state in" "" "Operational"
        jobControl -> p1Workers "Dispatches authorized work to" "" "Operational"
        p1Workers -> internetMail "Queries for current P1 validation evidence" "" "Operational"
        p1Workers -> jobControl "Returns progress, evidence, and artifacts to" "" "Operational"
        jobControl -> p2Smtp "Will dispatch eligible recipients to" "" "Ongoing"
        p2Smtp -> internetMail "Will perform conservative recipient handshakes against" "" "Ongoing"
        p2Smtp -> jobControl "Will return typed SMTP evidence to" "" "Ongoing"
    }

    views {
        systemContext trustSender "trustsender-system-context" {
            title "TrustSender.io System Context"
            description "People and external systems that interact with the public TrustSender.io platform."
            include *
            autoLayout lr
        }

        container trustSender "trustsender-container-view" {
            title "TrustSender.io Containers"
            description "Operational containers and the distinctly ongoing P2 SMTP evolution within TrustSender.io."
            include *
            autoLayout lr
        }

        styles {
            !include styles.dsl
        }
    }
}
