workspace "TrustSender.io Engineering Overview Flow Graph POC" "Presentation-only manual Flow Graph POC inspired by Structurizr Explore." {
    properties {
        "structurizr.inspection.model.relationship.technology" "info"
        "structurizr.inspection.views.styles.element.metadata" "info"
    }

    model {
        pocPlatformOperator = person "Platform Operator" "Operates and reviews the platform through approved interfaces." "POC,POC-User"
        pocCustomer = person "Customer" "Uses the TrustSender.io product through the public application." "POC,POC-User"

        pocGithubActions = softwareSystem "GitHub Actions" "Builds and deploys reviewed releases through the CI/CD workflow." "POC,POC-External"
        pocWordPressBlog = softwareSystem "WordPress Blog" "Serves public editorial content for the TrustSender.io blog." "POC,POC-Editorial"
        pocEdge = softwareSystem "Edge and Routing" "Routes public application, API, and blog traffic." "POC,POC-Edge"
        pocWebApplication = softwareSystem "Web Application" "Provides the public and authenticated TrustSender.io web experience." "POC,POC-Operational"
        pocApplicationApi = softwareSystem "Application API" "Provides authenticated application services and coordinates core platform workflows." "POC,POC-Operational"
        pocDatabase = softwareSystem "PostgreSQL Database" "Stores authoritative application, job, billing, and lifecycle data." "POC,POC-Operational"
        pocMicrosoftIdentity = softwareSystem "Microsoft Identity" "Provides Microsoft federated identity services." "POC,POC-External"
        pocGoogleIdentity = softwareSystem "Google Identity" "Provides Google federated identity services." "POC,POC-External"
        pocStripe = softwareSystem "Stripe" "Provides checkout and signed payment event services." "POC,POC-External"
        pocBrevo = softwareSystem "Brevo" "Provides transactional and operational email delivery." "POC,POC-External"
        pocJobControl = softwareSystem "Job Control Plane" "Coordinates validation job lifecycle, dispatch, progress, and evidence." "POC,POC-Operational"
        pocP1Workers = softwareSystem "Distributed P1 Worker Plane" "Operational" "POC,POC-Operational"
        pocP2Smtp = softwareSystem "P2 SMTP Execution Plane" "ONGOING" "POC,POC-Ongoing"
        pocInternetMail = softwareSystem "Internet Mail Infrastructure" "Represents external DNS and mail systems queried during email validation." "POC,POC-External"

        pocCustomer -> pocEdge "Accesses" "" "POC-Operational" {
            properties {
                "semanticDescription" "Accesses"
            }
        }
        pocPlatformOperator -> pocEdge "Accesses approved interfaces" "" "POC-Operational" {
            properties {
                "semanticDescription" "Accesses approved interfaces"
            }
        }
        pocGithubActions -> pocEdge "Builds and deploys reviewed releases" "" "POC-Operational" {
            properties {
                "semanticDescription" "Builds and deploys reviewed releases"
            }
        }
        pocEdge -> pocWebApplication "Routes application traffic" "" "POC-Operational" {
            properties {
                "semanticDescription" "Routes application traffic"
            }
        }
        pocEdge -> pocApplicationApi "Routes API traffic" "" "POC-Operational" {
            properties {
                "semanticDescription" "Routes API traffic"
            }
        }
        pocEdge -> pocWordPressBlog "Routes blog traffic" "" "POC-Operational" {
            properties {
                "semanticDescription" "Routes blog traffic"
            }
        }
        pocWebApplication -> pocApplicationApi "Uses" "" "POC-Operational" {
            properties {
                "semanticDescription" "Uses"
            }
        }
        pocApplicationApi -> pocDatabase "Reads and writes authoritative application data" "" "POC-Operational" {
            properties {
                "semanticDescription" "Reads and writes authoritative application data"
            }
        }
        pocApplicationApi -> pocJobControl "Submits and manages jobs" "" "POC-Operational" {
            properties {
                "semanticDescription" "Submits and manages jobs"
            }
        }
        pocJobControl -> pocDatabase "Reads and writes lifecycle state" "" "POC-Operational" {
            properties {
                "semanticDescription" "Reads and writes lifecycle state"
            }
        }
        pocJobControl -> pocP1Workers "Dispatches authorized work" "" "POC-Operational" {
            properties {
                "semanticDescription" "Dispatches authorized work"
            }
        }
        pocP1Workers -> pocJobControl "Returns progress, evidence, and artifacts" "" "POC-Operational" {
            properties {
                "semanticDescription" "Returns progress, evidence, and artifacts"
            }
        }
        pocP1Workers -> pocInternetMail "Queries for current P1 validation evidence" "" "POC-Operational" {
            properties {
                "semanticDescription" "Queries for current P1 validation evidence"
            }
        }
        pocApplicationApi -> pocGoogleIdentity "Uses for federated authentication" "" "POC-Operational" {
            properties {
                "semanticDescription" "Uses for federated authentication"
            }
        }
        pocApplicationApi -> pocMicrosoftIdentity "Uses for federated authentication" "" "POC-Operational" {
            properties {
                "semanticDescription" "Uses for federated authentication"
            }
        }
        pocApplicationApi -> pocStripe "Coordinates checkout and signed payment events" "" "POC-Operational" {
            properties {
                "semanticDescription" "Coordinates checkout and signed payment events"
            }
        }
        pocApplicationApi -> pocBrevo "Requests transactional and operational email" "" "POC-Operational" {
            properties {
                "semanticDescription" "Requests transactional and operational email"
            }
        }
        pocJobControl -> pocP2Smtp "Will dispatch eligible recipients" "" "POC-Ongoing" {
            properties {
                "semanticDescription" "Will dispatch eligible recipients"
            }
        }
        pocP2Smtp -> pocJobControl "Will return typed SMTP evidence" "" "POC-Ongoing" {
            properties {
                "semanticDescription" "Will return typed SMTP evidence"
            }
        }
        pocP2Smtp -> pocInternetMail "Will perform conservative recipient handshakes" "" "POC-Ongoing" {
            properties {
                "semanticDescription" "Will perform conservative recipient handshakes"
            }
        }
    }

    views {
        properties {
            "structurizr.locale" "en-GB"
            "structurizr.timezone" "UTC"
        }

        systemLandscape "trustsender-engineering-overview-manual-poc" {
            title "TrustSender.io Engineering Overview"
            description "P1 distributed validation is operational; P2 SMTP evolution remains ONGOING."
            include *
        }

        styles {
            element "POC" {
                shape Circle
                width 190
                height 190
                fontSize 18
                metadata false
                description false
            }

            element "POC-User" {
                background #243047
                color #F8FAFC
                stroke #93C5FD
                strokeWidth 2
            }

            element "POC-Operational" {
                background #1E293B
                color #F8FAFC
                stroke #38BDF8
                strokeWidth 2
            }

            element "POC-Edge" {
                background #164E63
                color #F8FAFC
                stroke #22D3EE
                strokeWidth 2
            }

            element "POC-Editorial" {
                background #312E81
                color #F8FAFC
                stroke #A5B4FC
                strokeWidth 2
            }

            element "POC-External" {
                background #303744
                color #F1F5F9
                stroke #94A3B8
                strokeWidth 2
            }

            element "POC-Ongoing" {
                background #78350F
                color #FFF7ED
                stroke #F59E0B
                strokeWidth 2
            }

            relationship "POC-Operational" {
                color #94A3B8
                style dashed
                thickness 2
                routing Direct
                fontSize 20
            }

            relationship "POC-Ongoing" {
                color #F59E0B
                style dashed
                thickness 2
                routing Direct
                fontSize 20
            }
        }
    }

    configuration {
        scope landscape
    }
}
