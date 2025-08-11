using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Shifter.Services;
using Shifter.Structs;
using Shifter.ViewModels;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel.Design.Serialization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.Models {
    public partial class ScdModel {

        /* Constructor*/
        public ScdModel(Session? session, SocketManager? socket) {
            _session = session!;
            _socket = socket!;
        }


        /** Member Variables **/
        readonly Session? _session;
        readonly SocketManager? _socket;
        readonly ObservableCollection<ShiftItem>? _shifts = [];
        readonly ObservableCollection<TodaysDutyInfo>? _todaysDuty = [];


        /** Member Method **/

        public ObservableCollection<ShiftItem> GetShifts() {
            return _shifts!;
        }

        public ObservableCollection<TodaysDutyInfo> GetTodaysDuty() {
            return _todaysDuty!;
        }

        /*
        {"data":[{"date":"2025-10-01","hours":8,"people":[{"grade":3,"name":"유예솜","staff_id":8}],"shift":"D"},{"date":"2025-10-01","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"E"},{"date":"2025-10-01","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"N"},{"date":"2025-10-01","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-02","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"D"},{"date":"2025-10-02","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"E"},{"date":"2025-10-02","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"N"},{"date":"2025-10-02","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박 주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1}],"shift":"O"},{"date":"2025-10-03","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"D"},{"date":"2025-10-03","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"E"},{"date":"2025-10-03","hours":8,"people":[{"grade":3,"name":"유예솜","staff_id":8}],"shift":"N"},{"date":"2025-10-03","hours":0,"people":[{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-04","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"D"},{"date":"2025-10-04","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"E"},{"date":"2025-10-04","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"N"},{"date":"2025-10-04","hours":0,"people":[{"grade":4,"name":"김유범","staff_id":4},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-05","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"D"},{"date":"2025-10-05","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"E"},{"date":"2025-10-05","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"N"},{"date":"2025-10-05","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-06","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"D"},{"date":"2025-10-06","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"E"},{"date":"2025-10-06","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"N"},{"date":"2025-10-06","hours":0,"people":[{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-07","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"D"},{"date":"2025-10-07","hours":8,"people":[{"grade":2,"name":"선서현","staff_id":2}],"shift":"E"},{"date":"2025-10-07","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"N"},{"date":"2025-10-07","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":5,"name":"오장 관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-08","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"D"},{"date":"2025-10-08","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"E"},{"date":"2025-10-08","hours":8,"people":[{"grade":2,"name":"선서현","staff_id":2}],"shift":"N"},{"date":"2025-10-08","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박주영","staff_id":9},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-09","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-09","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"E"},{"date":"2025-10-09","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"N"},{"date":"2025-10-09","hours":0,"people":[{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-10","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"D"},{"date":"2025-10-10","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"E"},{"date":"2025-10-10","hours":8,"people":[{"grade":3,"name":"유예솜","staff_id":8}],"shift":"N"},{"date":"2025-10-10","hours":0,"people":[{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-11","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"D"},{"date":"2025-10-11","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"E"},{"date":"2025-10-11","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":2,"name":"선서현","staff_id":2}],"shift":"N"},{"date":"2025-10-11","hours":0,"people":[{"grade":4,"name":"김 유범","staff_id":4},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-12","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"D"},{"date":"2025-10-12","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"E"},{"date":"2025-10-12","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"N"},{"date":"2025-10-12","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-13","hours":8,"people":[{"grade":3,"name":"유예솜","staff_id":8}],"shift":"D"},{"date":"2025-10-13","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"E"},{"date":"2025-10-13","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"N"},{"date":"2025-10-13","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-14","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"D"},{"date":"2025-10-14","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"E"},{"date":"2025-10-14","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"N"},{"date":"2025-10-14","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-15","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-15","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"E"},{"date":"2025-10-15","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"N"},{"date":"2025-10-15","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8}],"shift":"O"},{"date":"2025-10-16","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"D"},{"date":"2025-10-16","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"E"},{"date":"2025-10-16","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"N"},{"date":"2025-10-16","hours":0,"people":[{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예 솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":" 하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-17","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-17","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"E"},{"date":"2025-10-17","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"N"},{"date":"2025-10-17","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1}],"shift":"O"},{"date":"2025-10-18","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"D"},{"date":"2025-10-18","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"E"},{"date":"2025-10-18","hours":8,"people":[{"grade":3,"name":"유예솜","staff_id":8}],"shift":"N"},{"date":"2025-10-18","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-19","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"D"},{"date":"2025-10-19","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"E"},{"date":"2025-10-19","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"N"},{"date":"2025-10-19","hours":0,"people":[{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-20","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-20","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"E"},{"date":"2025-10-20","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"N"},{"date":"2025-10-20","hours":0,"people":[{"grade":5,"name":"김 대업","staff_id":10},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-21","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-21","hours":8,"people":[{"grade":2,"name":"선서현","staff_id":2}],"shift":"E"},{"date":"2025-10-21","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"N"},{"date":"2025-10-21","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박주영","staff_id":9},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희 라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-22","hours":8,"people":[{"grade":3,"name":"유예솜","staff_id":8}],"shift":"D"},{"date":"2025-10-22","hours":8,"people":[{"grade":2,"name":"선서현","staff_id":2}],"shift":"E"},{"date":"2025-10-22","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"N"},{"date":"2025-10-22","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":5,"name":"오장관","staff_id":5},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-23","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"D"},{"date":"2025-10-23","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"E"},{"date":"2025-10-23","hours":8,"people":[{"grade":3,"name":"유 예솜","staff_id":8}],"shift":"N"},{"date":"2025-10-23","hours":0,"people":[{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-24","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"D"},{"date":"2025-10-24","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"E"},{"date":"2025-10-24","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"N"},{"date":"2025-10-24","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-25","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"D"},{"date":"2025-10-25","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"E"},{"date":"2025-10-25","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"N"},{"date":"2025-10-25","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-26","hours":8,"people":[{"grade":4,"name":"김유범","staff_id":4}],"shift":"D"},{"date":"2025-10-26","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"E"},{"date":"2025-10-26","hours":8,"people":[{"grade":5,"name":"김대업","staff_id":10}],"shift":"N"},{"date":"2025-10-26","hours":0,"people":[{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-27","hours":8,"people":[{"grade":2,"name":"선서현","staff_id":2}],"shift":"D"},{"date":"2025-10-27","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"E"},{"date":"2025-10-27","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"N"},{"date":"2025-10-27","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":1,"name":"이보은","staff_id":6}],"shift":"O"},{"date":"2025-10-28","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-28","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"E"},{"date":"2025-10-28","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"N"},{"date":"2025-10-28","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-29","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"D"},{"date":"2025-10-29","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"E"},{"date":"2025-10-29","hours":8,"people":[{"grade":4,"name":"박주영","staff_id":9}],"shift":"N"},{"date":"2025-10-29","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":2,"name":"선서현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"},{"date":"2025-10-30","hours":8,"people":[{"grade":2,"name":"하진영","staff_id":7}],"shift":"D"},{"date":"2025-10-30","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"E"},{"date":"2025-10-30","hours":8,"people":[{"grade":1,"name":"유희라","staff_id":1}],"shift":"N"},{"date":"2025-10-30","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":3,"name":"박경태","staff_id":3},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서 현","staff_id":2},{"grade":5,"name":"오장관","staff_id":5},{"grade":3,"name":"유예솜","staff_id":8}],"shift":"O"},{"date":"2025-10-31","hours":8,"people":[{"grade":3,"name":"박경태","staff_id":3}],"shift":"D"},{"date":"2025-10-31","hours":8,"people":[{"grade":5,"name":"오장관","staff_id":5}],"shift":"E"},{"date":"2025-10-31","hours":8,"people":[{"grade":1,"name":"이보은","staff_id":6}],"shift":"N"},{"date":"2025-10-31","hours":0,"people":[{"grade":5,"name":"김대업","staff_id":10},{"grade":4,"name":"김유범","staff_id":4},{"grade":4,"name":"박주영","staff_id":9},{"grade":2,"name":"선서현","staff_id":2},{"grade":3,"name":"유예솜","staff_id":8},{"grade":1,"name":"유희라","staff_id":1},{"grade":2,"name":"하진영","staff_id":7}],"shift":"O"}],"message":"근무표 생성 완료","protocol":"gen_timeTable","resp":"success"}
        */
        /* Protocol - gen_timeTable */
        public async Task<ObservableCollection<StaffSchedule>> GenTimeTableAsync(int? year, int? month) {
            int admin_uid = _session!.GetCurrentAdminId();
            int team_uid = _session!.GetCurrentTeamId();

            /* [1] new json */
            JObject sendJson = new JObject {
            { "protocol", "gen_timeTable" },
            { "data", new JObject {
                { "admin_uid", admin_uid },
                { "team_uid",  team_uid },
                { "req_year",  year.ToString() },
                { "req_month", month.ToString() }
                }
                }
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            /* [5] Parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if (protocol == "gen_timeTable" && resp == "success") {
                // 성공적으로 테이블 생성됨
                Console.WriteLine("TimeTable generated successfully for {0}-{1}.", year, month);

                var result = new ObservableCollection<StaffSchedule>();
                var byId = new Dictionary<int, StaffSchedule>();
                int daysInMonth = DateTime.DaysInMonth(year!.Value, month!.Value);

                JToken dataTok = recvJson["data"]!;
                var items = dataTok is JArray arr ? arr
                          : dataTok["schedules"] is JArray arr2 ? arr2
                          : new JArray();

                foreach (var item in items) {
                    var dateStr = (string)item["date"]!;
                    var shift = (string)item["shift"]!;
                    int day = DateTime.Parse(dateStr).Day;

                    foreach (var p in (JArray)item["people"]!) {
                        int staffId = (int)p["staff_id"]!;
                        string name = (string)p["name"]!;

                        if (!byId.TryGetValue(staffId, out var staff)) {
                            staff = new StaffSchedule { StaffId = staffId, Name = name };
                            for (int d = 1; d <= daysInMonth; d++)
                                staff.DailyShifts.Add(new ScheduleCell { Day = d });
                            byId[staffId] = staff;
                            result.Add(staff);
                        }
                        staff.DailyShifts[day - 1].ShiftCode = shift; // "D/E/N/O"
                    }
                }
                return result;
            }
            else {
                // 실패 처리
                Console.WriteLine("Failed to generate TimeTable: {0}", recvJson["message"]!.ToString());
                return [];
            }
        }


        /* Protocol - check_today_duty */
        public async Task<List<TodaysDutyInfo>> CheckTodayDutyAsync() {
            Console.WriteLine("[ScdModel] Executed CheckTodayDutyAsync()");

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "check_today_duty" },
                { "data", new JObject {
                    { "date", DateTime.Now.Date.ToString()[..10] },
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            /* [5] Parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            var result = new List<TodaysDutyInfo>();
            if (protocol == "check_today_duty" && resp == "success") {

                if ((string)recvJson["protocol"]! == "check_today_duty" &&
                    (string)recvJson["resp"]! == "success") {
                    foreach (JObject duty in (JArray)recvJson["data"]!) {
                        result.Add(new TodaysDutyInfo
                        {
                            Shift = duty.Value<string>("shift") ?? "",
                            StaffName = duty["staff"]?.ToObject<string[]>() ?? Array.Empty<string>()
                        });
                    }
                }
            }
            return result;
        }


        /* protocol req_shift_info */
        public async Task ReqShiftInfo() {
            Console.WriteLine("[ScdModel] Executed ReqShiftInfo()");

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "req_shift_info" },
                { "data", new JObject {
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();

            /* [5] Parse the data. */
            JObject recvJson = JObject.Parse(recvItem.json);

            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();
            var data = recvJson["data"]!;

            if (protocol == "req_shift_info" && resp == "success") {
                Console.WriteLine("Shift information requested successfully.");

                _shifts!.Clear(); // Clear existing shifts before adding new ones
                foreach (var shift in data["shift_info"]!) {
                    ShiftItem shiftItem = new ShiftItem()
                    {
                        ShiftType = shift["duty_type"]!.ToString(),
                        StartTime = shift["start_time"]!.ToString(),
                        EndTime = shift["end_time"]!.ToString(),
                        DutyHours = shift["duty_hours"]!.ToObject<int>()
                    };
                    _shifts.Add(shiftItem);
                }
            }
            else {
                // 실패 처리
                Console.WriteLine("Failed to request shift information: {0}", recvJson["message"]!.ToString());

            }
        }


        /* protocol ask_timetable_admin */
        /*
         * {
            "protocol" : "ask_timetable_admin"
            "data" : {
                "req_year" : "yyyy",
                "req_month": "MM",
                "team_uid" : 0,
                }
           }
         */
        public async Task AskTimeTableAdminAsync(int year, int month) {
            Console.WriteLine("[ScdModel] Executed AskTimeTableAdminAsync()");

            /* [1] new json */
            JObject sendJson = new JObject {
                { "protocol", "ask_timetable_admin" },
                { "data", new JObject {
                    { "req_year", year.ToString() },
                    { "req_month", month.ToString() },
                    { "team_uid", _session!.GetCurrentTeamId() }
                }}
            };

            /* [2] Put json in WorkItem */
            WorkItem sendItem = new WorkItem
            {
                json = JsonConvert.SerializeObject(sendJson),
                payload = [],
                path = ""
            };

            /* [3] Send the created WorkItem */
            await _socket!.SendAsync(sendItem);

            /* [4] Create WorkItem response & receive data from the socket. */
            WorkItem recvItem = await _socket.ReceiveAsync();
            JObject recvJson = JObject.Parse(recvItem.json);
            byte[] payload = recvItem.payload;
            string path = recvItem.path;

            /* [5] Parse the data. */
            string protocol = recvJson["protocol"]!.ToString();
            string resp = recvJson["resp"]!.ToString();

            if (protocol == "ask_timetable_admin" && resp == "success") {

            }
            else {
                // 실패 처리
                Console.WriteLine("Failed to request TimeTable: {0}", recvJson["message"]!.ToString());
            }
        }
    }


    /*** Today's Duty Info ***/
    public partial class TodaysDutyInfo : ObservableObject {
        [ObservableProperty] private string? shift;          // 근무조
        [ObservableProperty] private string[]? staffName;     // 직원명
    }


    /*** Class Staff Schedule ***/
    public partial class StaffSchedule : ObservableObject {

        /** Constructor **/
        public StaffSchedule() {
            DailyShifts.CollectionChanged += (s, e) => {
                if (e.NewItems != null)
                    foreach (ScheduleCell cell in e.NewItems)
                        cell.ShiftCodeChanged += OnCellShiftChanged;
                if (e.OldItems != null)
                    foreach (ScheduleCell cell in e.OldItems)
                        cell.ShiftCodeChanged -= OnCellShiftChanged;
            };
        }

        /* Member Variables */
        public string Name { get; set; } = string.Empty;
        public ObservableCollection<ScheduleCell> DailyShifts { get; set; } = new();
        // 동적 통계용 딕셔너리
        public ObservableCollection<KeyValuePair<string, int>> ShiftCodeCounts { get; set; } = new();
        public event EventHandler? ShiftChanged;
        public Action? UpdateDailyStatsCallback { get; set; }


        private void OnCellShiftChanged(object? sender, EventArgs e) {
            UpdateShiftCounts();
            OnPropertyChanged(nameof(TotalWorkingHours));
            OnPropertyChanged(nameof(TotalEmptyDays));
            UpdateDailyStatsCallback?.Invoke(); // ViewModel에 직접 요청
        }


        public void UpdateShiftCounts() {
            // 1. 임시 Dictionary로 그룹핑된 카운트 계산
            var tempDict = DailyShifts
                .GroupBy(c => c.ShiftCode)
                .Where(g => !string.IsNullOrWhiteSpace(g.Key))
                .ToDictionary(g => g.Key!, g => g.Count());

            // 2. 순서 맞춰 다시 채우기
            ShiftCodeCounts.Clear();

            foreach (var shift in MdfScdViewModel.ShiftCodes) {
                tempDict.TryGetValue(shift, out int count);
                ShiftCodeCounts.Add(new KeyValuePair<string, int>(shift, count));
            }

            OnPropertyChanged(nameof(ShiftCodeCounts));
        }

        public int TotalWorkingHours =>
            DailyShifts.Sum(c =>
                MdfScdViewModel.ShiftWorkingHoursMap.TryGetValue(c.ShiftCode ?? "", out int hours) ? hours : 0);

        public int TotalEmptyDays =>
            DailyShifts.Count(c => string.IsNullOrWhiteSpace(c.ShiftCode));

        public int StaffId { get; internal set; }
    }


    /*** Class Schedule Cell ***/
    public partial class ScheduleCell : ObservableObject {

        /** Member Variables **/
        [ObservableProperty] private int day;
        private string shiftCode = "";
        public string ShiftCode {
            get => shiftCode;
            set {
                if (SetProperty(ref shiftCode, value)) {
                    ShiftCodeChanged?.Invoke(this, EventArgs.Empty);
                }
            }
        }
        public event EventHandler? ShiftCodeChanged;
    }


    /*** Class ShiftHeader ***/
    public class ShiftHeader {
        public string DisplayName { get; set; } = "";   // 예: "Total D"
        public string ShiftCode { get; set; } = "";     // 예: "D"
    }


    /*** Class Daily Shift Status ***/
    public class DailyShiftStats : ObservableObject {
        public int Day { get; set; }

        // shift 코드 → 해당 일에 몇 명이 이 교대를 했는지
        public Dictionary<string, int> ShiftCounts { get; set; } = new();
    }

}
