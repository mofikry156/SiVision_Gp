########################################################################
# m2_grid_dynamic_autovia_seed_from_report_FULL_FIXED6.tcl
# FIX: If trial via causes strap net to match usedNets, delete/recreate strap and continue
# this script works by placing a CreatVia at the start of circuit, starting from the right edge of the cicruit,
# the CreatVia will increment by 0.074 in the left direction of X-axis to cover the whole metal strap, it will comapre the name of the net to the previous 2 nets
# if it didn't find any unique nets, it will remove the metal strap entirley
#the m2_grid_report.txt is used to find the top right corner, which indicates the start of a new row, it will also be used to indicate the strating point of each via12 exactly
#after a CreatVia12 finds a unique net, it is removed and then AutoVia are placed to remove the headache of DRC violations
########################################################################

# ----------------------------
# USER SETTINGS
# ----------------------------
set REPORT_FILE "/home/users/svgplayout2601mofikry/gonna_work/m2_grid_report.txt"

set LPP_M2 {M2 drawing}

# Trial probe via (createVia)
set VIA_DEF_NAME "VIA12"
set VIA_ORIENT   "R0"
set VIA_PARAMS   {}          ;# e.g. {{cutRows 10} {cutColumns 10}}

# APPROACH mapping
set XFR_A1_TOP3  0.009
set XFR_A1_BOT3  0.046
set XFR_A2_TOP3  0.046
set XFR_A2_BOT3  0.009

# Left boundary offset from left edge of strap
set X_FROM_LEFT  0.02

# Seed stepping
set STEP_X         0.074
set MAX_SEED_TRIES 3000

# autoVia capture box around each (x,yc)
set AUTOVIA_BOX_W  0.034
set AUTOVIA_BOX_H  0.020

# ----------------------------
# HELPERS
# ----------------------------
proc _safeDestroy {obj} {
  if {$obj eq ""} { return }
  catch { db::destroy $obj }
  catch { le::delete $obj }
}

proc _isNumber {s} {
  return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s]
}

proc _tryGetNetName {obj} {
  if {$obj eq ""} { return "" }
  foreach expr {
    {db::getAttr net.name -of $obj}
    {db::getAttr netName  -of $obj}
    {db::getAttr net      -of $obj}
  } {
    set v ""
    if {![catch {set v [eval $expr]}]} {
      if {$v eq ""} { continue }
      if {[string match "oa:*" $v]} {
        set nm ""
        if {![catch {set nm [db::getAttr name -of $v]}]} {
          if {$nm ne ""} { return $nm }
        }
      } else {
        return $v
      }
    }
  }
  return ""
}

proc _createViaPointOrient {design pt viaDefName orient params} {
  set v ""
  if {$params eq ""} {
    if {[catch { set v [le::createVia -design $design -definition $viaDefName -origin $pt -orient $orient] } err]} {
      return ""
    }
  } else {
    if {[catch { set v [le::createVia -design $design -definition $viaDefName -origin $pt -orient $orient -params $params] } err]} {
      return ""
    }
  }
  return $v
}

proc _ptToBox {x y w h} {
  set x1 [expr {$x - $w/2.0}]
  set x2 [expr {$x + $w/2.0}]
  set y1 [expr {$y - $h/2.0}]
  set y2 [expr {$y + $h/2.0}]
  return [list [list $x1 $y1] [list $x2 $y2]]
}

proc _autoViaBox {design box netFilter} {
  set v ""
  if {[catch {
    set v [le::autoVia -box $box -design $design \
      -nets $netFilter \
      -sameNetOnly true \
      -createMetalShape false \
      -allowStackedVia true \
      -fitToOverlappedArea true]
  } err]} {
    return ""
  }
  return $v
}

proc _autoViaPoint {design pt netFilter} {
  set v ""
  if {[catch {
    set v [le::autoVia -point $pt -design $design \
      -nets $netFilter \
      -sameNetOnly true \
      -createMetalShape false \
      -allowStackedVia true \
      -fitToOverlappedArea true]
  } err]} {
    return ""
  }
  return $v
}

proc _findStrapRectByBBox {design lpp xll yll xur yur} {
  set tol 0.0005
  set sh [db::getShapes -of $design -lpp $lpp -filter {%type=="Rect"}]
  db::foreach s $sh {
    set bb ""
    if {[catch {set bb [db::getAttr bBox -of $s]}]} { continue }
    set llx [lindex [lindex $bb 0] 0]
    set lly [lindex [lindex $bb 0] 1]
    set urx [lindex [lindex $bb 1] 0]
    set ury [lindex [lindex $bb 1] 1]
    if {abs($llx-$xll) < $tol && abs($lly-$yll) < $tol && abs($urx-$xur) < $tol && abs($ury-$yur) < $tol} {
      return $s
    }
  }
  return ""
}

# NEW: Recreate strap to reset its net
proc _recreateStrap {design lpp xll yll xur yur oldObj} {
  _safeDestroy $oldObj
  set box [list [list $xll $yll] [list $xur $yur]]
  set newObj ""
  if {[catch { set newObj [le::createRectangle $box -design $design -lpp $lpp] } err]} {
    puts "WARN: failed to recreate strap rect BB=($xll $yll)-($xur $yur) err=$err"
    return ""
  }
  return $newObj
}

# NEW: Get net from strap object
proc _getStrapNet {strapObj} {
  if {$strapObj eq ""} { return "" }
  return [_tryGetNetName $strapObj]
}

# ----------------------------
# REPORT PARSER
# ----------------------------
proc _parseReportByRow {fname} {
  if {![file exists $fname]} { error "REPORT_FILE not found: $fname" }

  array set rowApproach {}
  array set rowStraps {}

  set fp [open $fname r]
  while {[gets $fp line] >= 0} {
    set raw $line
    set line [string trim $line]
    if {$line eq ""} continue

    # If comment, still try to parse approach headers from it
    if {[string match "#*" $line]} {
      if {[regexp {ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+APPROACH=([A-Z0-9_]+)} $line -> ridx topVal appr]} {
        set rowApproach($ridx) $appr
      } elseif {[regexp {ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+(APPROACH[0-9]+)} $line -> ridx topVal appr2]} {
        set rowApproach($ridx) $appr2
      }
      continue
    }

    # Non-comment header forms
    if {[regexp {^ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+APPROACH=([A-Z0-9_]+)} $line -> ridx topVal appr]} {
      set rowApproach($ridx) $appr
      continue
    }
    if {[regexp {^ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+(APPROACH[0-9]+)} $line -> ridx topVal appr2]} {
      set rowApproach($ridx) $appr2
      continue
    }

    # Strap line
    if {[regexp {^ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+off=([-\d\.]+)\s+Yc=([-\d\.]+)\s+BB=\(([-\d\.]+)\s+([-\d\.]+)\)-\(([-\d\.]+)\s+([-\d\.]+)\)} \
         $line -> ridx topVal offVal yc xll yll xur yur]} {

      foreach v [list $topVal $offVal $yc $xll $yll $xur $yur] {
        if {$v eq "" || ![_isNumber $v]} {
          puts "WARN: Skipping malformed strap line: $raw"
          continue 2
        }
      }

      set strap [dict create \
        row $ridx top $topVal off $offVal yc $yc \
        xll $xll yll $yll xur $xur yur $yur \
      ]
      if {![info exists rowStraps($ridx)]} { set rowStraps($ridx) {} }
      lappend rowStraps($ridx) $strap
      continue
    }
  }
  close $fp

  return [list [array get rowApproach] [array get rowStraps]]
}

proc _sortStrapsByOffAsc {strapList} {
  set tmp {}
  foreach s $strapList {
    set off [dict get $s off]
    lappend tmp [list $off $s]
  }
  set tmp [lsort -real -increasing -index 0 $tmp]
  set out {}
  foreach pair $tmp { lappend out [lindex $pair 1] }
  return $out
}

proc _getXFromRightForGroup {approach groupName} {
  if {$approach eq "APPROACH2"} {
    if {$groupName eq "TOP3"} { return $::XFR_A2_TOP3 }
    return $::XFR_A2_BOT3
  }
  if {$groupName eq "TOP3"} { return $::XFR_A1_TOP3 }
  return $::XFR_A1_BOT3
}

# ----------------------------
# MODIFIED: Find unique seed with strap recreation logic
# ----------------------------
proc _findUniqueSeedOnStrap {design strapDict approach groupName usedNets strapObjVar} {
  upvar $strapObjVar strapObj
  
  set xll [dict get $strapDict xll]
  set yll [dict get $strapDict yll]
  set xur [dict get $strapDict xur]
  set yur [dict get $strapDict yur]
  set yc  [dict get $strapDict yc]

  set xFromRight [_getXFromRightForGroup $approach $groupName]
  set xStart [expr {$xur - $xFromRight}]
  set xStop  [expr {$xll + $::X_FROM_LEFT}]
  if {$xStart <= $xStop} {
    return [list FAIL "" ""]
  }

  set tries 0
  for {set x $xStart} {$x >= $xStop} {set x [expr {$x - $::STEP_X}]} {
    incr tries
    if {$tries > $::MAX_SEED_TRIES} { break }

    set pt [list $x $yc]
    
    # Place trial via
    set vTrial [_createViaPointOrient $design $pt $::VIA_DEF_NAME $::VIA_ORIENT $::VIA_PARAMS]
    if {$vTrial eq ""} { continue }

    set viaNet [_tryGetNetName $vTrial]
    _safeDestroy $vTrial
    
    if {$viaNet eq ""} { continue }

    # Check if via net is already used in group
    if {[lsearch -exact $usedNets $viaNet] != -1} { 
      # Via net already used, but check if strap got contaminated
      set strapNet [_getStrapNet $strapObj]
      
      if {$strapNet ne "" && [lsearch -exact $usedNets $strapNet] != -1} {
        # STRAP GOT CONTAMINATED! Delete and recreate it
        puts "    CONTAMINATION: Trial via at X=$x caused strap to get net '$strapNet' (already used)"
        set strapObj [_recreateStrap $design $::LPP_M2 $xll $yll $xur $yur $strapObj]
        if {$strapObj eq ""} {
          return [list FAIL "" ""]
        }
        puts "    RECREATED: Strap reset, continuing search..."
      }
      continue
    }

    # Found unique net - this is our seed
    return [list OK $viaNet $x]
  }

  return [list FAIL "" ""]
}

proc _placeAutoViasAlongStrap {design strapDict seedX seedNet} {
  set xll [dict get $strapDict xll]
  set yc  [dict get $strapDict yc]
  set xStop [expr {$xll + $::X_FROM_LEFT}]

  set count 0
  set viaCount 0
  
  # Place seed via first
  set seedVia [_autoViaPoint $design [list $seedX $yc] $seedNet]
  if {$seedVia ne ""} {
    incr viaCount
  }
  
  # Fill remaining locations
  for {set x [expr {$seedX - $::STEP_X}]} {$x >= $xStop} {set x [expr {$x - $::STEP_X}]} {
    set box [_ptToBox $x $yc $::AUTOVIA_BOX_W $::AUTOVIA_BOX_H]
    set result [_autoViaBox $design $box $seedNet]
    if {$result ne ""} {
      incr viaCount
    }
    incr count
  }
  puts "    autoVia: attempts=$count placed=$viaCount (seedX=$seedX yc=$yc net=$seedNet)"
}

# ----------------------------
# MAIN
# ----------------------------
proc run_m2_grid_dynamic_autovia {} {
  set ctx    [de::getActiveContext]
  set design [db::getAttr editDesign -of $ctx]

  if {$design eq ""} { error "No edit design found." }

  # sanity check via def exists
  set _t ""
  if {[catch {set _t [le::createVia -design $design -definition $::VIA_DEF_NAME -origin {0 0} -orient $::VIA_ORIENT]} err]} {
    error "VIA_DEF_NAME '$::VIA_DEF_NAME' invalid in your tech: $err"
  }
  _safeDestroy $_t

  lassign [_parseReportByRow $::REPORT_FILE] approachArr strapsArr
  array set rowApproach $approachArr
  array set rowStraps   $strapsArr

  # de-dup map per run
  catch {unset ::_seenStraps}
  array set ::_seenStraps {}

  set kept 0
  set deleted 0
  set warn 0
  set contaminated 0

  foreach ridx [lsort -integer [array names rowStraps]] {
    set approach "UNKNOWN"
    if {[info exists rowApproach($ridx)]} { set approach $rowApproach($ridx) }

    # EDGE rows => skip
    if {[string match "EDGE*" $approach] || $approach eq "EDGE"} {
      puts "ROW $ridx: approach=$approach => SKIP (manual placement)"
      continue
    }

    set straps [_sortStrapsByOffAsc $rowStraps($ridx)]
    set n [llength $straps]
    if {$n == 0} continue

    set topN 3
    if {$n < 3} { set topN $n }
    set botN 3
    if {$n < 3} { set botN $n }

    set top3 [lrange $straps 0 [expr {$topN-1}]]
    set bot3 [lrange $straps [expr {$n-$botN}] [expr {$n-1}]]

    puts "ROW $ridx: approach=$approach straps=$n => TOP3=[llength $top3] BOT3=[llength $bot3]"

    set usedTop {}
    set usedBot {}

    foreach groupName {TOP3 BOT3} {
      if {$groupName eq "TOP3"} {
        set groupList $top3
      } else {
        set groupList $bot3
      }

      foreach strap $groupList {
        # de-dup if top3/bot3 overlap (n<6)
        set strapKey "[dict get $strap xll],[dict get $strap yll],[dict get $strap xur],[dict get $strap yur]"
        if {[info exists ::_seenStraps($ridx,$strapKey)]} {
          continue
        }
        set ::_seenStraps($ridx,$strapKey) 1

        set xll [dict get $strap xll]
        set yll [dict get $strap yll]
        set xur [dict get $strap xur]
        set yur [dict get $strap yur]

        set strapObj [_findStrapRectByBBox $design $::LPP_M2 $xll $yll $xur $yur]
        if {$strapObj eq ""} {
          incr warn
          puts "WARN: ROW $ridx $groupName strap BB=($xll $yll)-($xur $yur) not found; skipping."
          continue
        }

        if {$groupName eq "TOP3"} {
          set used $usedTop
        } else {
          set used $usedBot
        }

        # MODIFIED: Pass strapObj by reference so it can be recreated
        lassign [_findUniqueSeedOnStrap $design $strap $approach $groupName $used strapObj] status seedNet seedX
        
        if {$status ne "OK"} {
          puts "  DELETE: ROW $ridx $groupName no unique net found on strap BB=($xll $yll)-($xur $yur)"
          _safeDestroy $strapObj
          incr deleted
          continue
        }

        puts "  ACCEPT: ROW $ridx $groupName net=$seedNet seedX=$seedX BB=($xll $yll)-($xur $yur)"
        
        _placeAutoViasAlongStrap $design $strap $seedX $seedNet

        if {$groupName eq "TOP3"} {
          lappend usedTop $seedNet
        } else {
          lappend usedBot $seedNet
        }

        incr kept
      }
    }
  }

  puts "DONE: keptStraps=$kept deletedStraps=$deleted warns=$warn"
}

# Run
run_m2_grid_dynamic_autovia

