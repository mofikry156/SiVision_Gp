# ----------------------------
# USER SETTINGS
# ----------------------------
set M3_FILE "/home/users/svgplayout2601mofikry/gonna_work/m3_coords.txt"
set M2_FILE "/home/users/svgplayout2601mofikry/gonna_work/current_m2_metals_with_nets.txt"

# ----------------------------
# LOGIC
# ----------------------------
proc place_via23_from_files {} {
    set design [ed]
    if {$design eq ""} { error "No active design found." }

    # 1. Parse M3 file into a dictionary: net -> {XLL XUR}
    # We use this to know where the vertical M3 pillars are.
    set m3_data [dict create]
    set fp3 [open $::M3_FILE r]
    while {[gets $fp3 line] >= 0} {
        set line [string trim $line]
        if {[regexp {^\d+\s+(\S+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)} $line -> net xll yll xur yur]} {
            dict set m3_data $net [list $xll $xur]
        }
    }
    close $fp3

    # 2. Parse M2 file and create Vias at intersections
    set fp2 [open $::M2_FILE r]
    set via_count 0

    while {[gets $fp2 line] >= 0} {
        set line [string trim $line]
        # Regex to match: idx net xll yll xur yur yc
        if {[regexp {^\d+\s+(\S+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)} $line -> net m2_xll m2_yll m2_xur m2_yur m2_yc]} {
            
            # Find the corresponding M3 for this net
            if {[dict exists $m3_data $net]} {
                set m3_coords [dict get $m3_data $net]
                set m3_xll [lindex $m3_coords 0]
                set m3_xur [lindex $m3_coords 1]

                # The Intersection Box:
                # X comes from M3 (Vertical pillar width)
                # Y comes from M2 (Horizontal strap height)
                set bBox [list [list $m3_xll $m2_yll] [list $m3_xur $m2_yur]]

                # Call AutoVia
                puts "Placing Via23 for Net: $net at Box: $bBox"
                if {[catch {
                    le::autoVia -box $bBox \
                                -design $design \
                                -nets $net \
                                -sameNetOnly true \
                                -fitToOverlappedArea true \
                                -allowStackedVia true
                } err]} {
                    puts "WARN: Failed to place via for $net: $err"
                } else {
                    incr via_count
                }
            }
        }
    }
    close $fp2

    puts "DONE: Created $via_count AutoVias."
}

# Run it
place_via23_from_files
