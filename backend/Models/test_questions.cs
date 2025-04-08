using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class test_questions
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public int? test_id { get; set; }
        [ForeignKey("test_id")]
        public tests test { get; set; }

        public int? question_id { get; set; }
        [ForeignKey("question_id")]
        public questions question { get; set; }
    }
}
