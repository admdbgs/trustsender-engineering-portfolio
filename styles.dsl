element "Person" {
    shape Person
    background #243047
    color #F8FAFC
    stroke #93C5FD
}

element "Software System" {
    background #172033
    color #F8FAFC
    stroke #60A5FA
}

element "Container" {
    background #1E293B
    color #F8FAFC
    stroke #64748B
}

element "External" {
    background #303744
    color #F1F5F9
    stroke #94A3B8
}

element "Operational" {
    stroke #38BDF8
}

element "Ongoing" {
    background #78350F
    color #FFF7ED
    stroke #F59E0B
}

element "Data Store" {
    shape Cylinder
}

element "Edge" {
    background #164E63
    stroke #22D3EE
}

element "Editorial" {
    background #312E81
    stroke #A5B4FC
}

relationship "Operational" {
    color #94A3B8
    style solid
    thickness 2
}

relationship "Ongoing" {
    color #F59E0B
    style dashed
    thickness 2
}
