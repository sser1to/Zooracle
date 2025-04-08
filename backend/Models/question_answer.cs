using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class question_answer
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public int? question_id { get; set; }
        [ForeignKey("question_id")]
        public questions question { get; set; }

        public int? answer_id { get; set; }
        [ForeignKey("answer_id")]
        public answer_options answer_option { get; set; }
    }
}
